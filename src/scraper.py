"""
Main scraper class for collecting BBB roofing contractor data
"""

import logging
import time
import json
import re
import csv
from typing import List, Dict, Optional, Set
from pathlib import Path
import requests
from urllib.parse import urlencode
from src.utils import clean_obfuscated_email

from config import (
    BBB_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY,
    RECORDS_PER_PAGE, KEYWORD_FILTERS, LOWER_48_STATES, USER_AGENT,
    RATE_LIMIT, PROXY, CSV_COLUMNS
)
from src.utils import contains_keyword, normalize_state, setup_logging, clean_html_tags

logger = logging.getLogger("bbb_scraper")


class BBBScraper:
    """Web scraper for BBB.org roofing contractor data"""
    
    def __init__(self, csv_path: Optional[str] = None):
        """Initialize the scraper
        
        Args:
            csv_path: Optional path to existing CSV file to avoid duplicates
        """
        self.base_url = BBB_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.last_request_time = 0
        self.valid_records = []
        self.invalid_records = []
        self.csv_path = csv_path
        self.existing_business_names: Set[str] = set()
        
        # Load existing business names from CSV if path provided
        if csv_path:
            self._load_existing_business_names()
        
    def _load_existing_business_names(self) -> None:
        """Load all existing business names from CSV file to prevent duplicates
        
        Normalizes names by converting to lowercase and stripping HTML tags
        """
        if not self.csv_path or not Path(self.csv_path).exists():
            return
        
        try:
            with open(self.csv_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    business_name = row.get("business_name", "").strip()
                    if business_name:
                        # Normalize name for comparison (same as in scrape_city_search_url)
                        name_key = clean_html_tags(business_name).strip().lower()
                        self.existing_business_names.add(name_key)
            
            logger.info(f"Loaded {len(self.existing_business_names)} existing business names from CSV")
        except Exception as e:
            logger.warning(f"Failed to load existing business names from CSV: {e}")
    
    def _respect_rate_limit(self):
        """Implement rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < (1 / RATE_LIMIT):
            time.sleep((1 / RATE_LIMIT) - elapsed)
        self.last_request_time = time.time()
    
    def is_valid_businessName(self, business_name: str = "") -> bool:
        """
        Validate if a business name meets inclusion criteria
        
        Args:
            business_name: Business name
            
        Returns:
            True if business_name meets validation
        """
        # Check business name contains required keyword
        if not contains_keyword(business_name, KEYWORD_FILTERS):
            logger.info(f"---!!! Excluding Business Name '{business_name}' - does not match keywords")
            return False
        
        return True
    
    def extract_business_data(self, record: Dict, source_url: str = "") -> Dict:
        """
        Extract and normalize business data from BBB record
        
        Args:
            record: Business record from BBB
            source_url: URL of the source page
            
        Returns:
            Cleaned business data dictionary
        """
        # Extract phone numbers
        phones = record.get("phone") or []
        phone = phones[0] if isinstance(phones, list) and phones else ""
        
        # Extract categories
        categories = record.get("categories") or []
        category_names = [cat.get("name", "") for cat in categories]
        categories_str = "; ".join(category_names) if category_names else ""
        
        # Build source URL
        report_url = (record.get("reportUrl") or "")
        if report_url and not report_url.startswith("http"):
            report_url = f"https://www.bbb.org{report_url}"
        
        business_data = {
            "business_name": clean_html_tags(record.get("businessName") or ""),
            "street_address": (record.get("address") or "").strip(),
            "city": (record.get("city") or "").strip(),
            "state": (record.get("state") or "").strip().upper(),
            "postal_code": (record.get("postalcode") or "").strip(),
            "phone": phone.strip() if phone else "",
            "email": "",  # may be available on detail page
            "website": "",  # may be available on detail page
            "entity_type": "",
            "business_started": "",
            "incorporated_date": "",
            "principal_contact": "",
            "business_categories": categories_str,
            "source_url": report_url
        }

        # If there is a detail/report URL, try to fetch the detailed page and extract
        # additional fields such as principal contacts, dates, entity type, website,
        # phone and email.
        if report_url:
            try:
                self._respect_rate_limit()
                resp = self.session.get(report_url, timeout=REQUEST_TIMEOUT,
                                        proxies=PROXY if PROXY else None)
                if resp.status_code == 200:
                    detail_html = resp.text
                    # Try to extract embedded JSON state from the detail page
                    detail_data = None
                    additional_data = None
                    try:
                        # Prefer schema.org JSON-LD if present (contains reliable employee info)
                        m2 = re.search(r'<script[^>]*type\s*=\s*["\']?application/ld\+json["\']?[^>]*>(.*?)</script>', detail_html, re.DOTALL | re.IGNORECASE)
                        if m2:
                            try:
                                additional_data = json.loads(m2.group(1))
                            except Exception:
                                additional_data = None

                        # Fallback to window.__PRELOADED_STATE__ if no JSON-LD
                        m = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.*?})\s*;', detail_html, re.DOTALL)
                        if m:
                            detail_data = json.loads(m.group(1))
                        else:
                            detail_data = None
                    except Exception:
                        detail_data = None

                    # Helper to recursively find a key in nested dicts/lists
                    def find_key(obj, key):
                        if isinstance(obj, dict):
                            if key in obj:
                                return obj[key]
                            for v in obj.values():
                                res = find_key(v, key)
                                if res is not None:
                                    return res
                        elif isinstance(obj, list):
                            for item in obj:
                                res = find_key(item, key)
                                if res is not None:
                                    return res
                        return None
                    
                    if additional_data:
                        # Principal contact(s) - Extract from contactInformation
                        employees = find_key(additional_data, "employee") or []
                        if isinstance(employees, list):
                            contacts = []
                            for emp in employees:
                                if not isinstance(emp, dict):
                                    continue
                                name_parts = [
                                    emp.get("honorificPrefix"),
                                    emp.get("givenName"),
                                    emp.get("familyName"),
                                ]
                                name = " ".join(p.strip() for p in name_parts if p)
                                job_title = (emp.get("jobTitle") or "").strip()
                                if job_title:
                                    name = f"{name}, {job_title}"
                                if name:
                                    contacts.append(name)
                            if contacts:
                                business_data["principal_contact"] = "|".join(contacts)
                            logger.info(f"------ Extracted principal contacts: {contacts}")

                    if detail_data:
                        # Dates
                        dates = find_key(detail_data, "dates") or {}
                        if isinstance(dates, dict):
                            business_data["incorporated_date"] = (dates.get("incorporated") or "").strip()
                            business_data["business_started"] = (dates.get("businessStart") or "").strip()

                        # Entity type
                        type_of_entity = find_key(detail_data, "typeOfEntity") or {}
                        if isinstance(type_of_entity, dict):
                            business_data["entity_type"] = (type_of_entity.get("name") or "").strip()

                        # Extract email and websites from contactInformation (primary source)
                        contact_info = find_key(detail_data, "contactInformation")
                        if contact_info and isinstance(contact_info, dict):
                            email = clean_obfuscated_email((contact_info.get("emailAddress") or "").strip())
                            if email:
                                business_data["email"] = email
                                logger.info(f"------ Extracted email: {email}")
                            
                            additional_websites = contact_info.get("additionalWebsiteAddresses", [])
                            if isinstance(additional_websites, list) and additional_websites:
                                websites = []
                                for website in additional_websites:
                                    website = website.strip()
                                    if website:
                                        websites.append(website)
                                if websites:
                                    business_data["website"] = "|".join(websites)
                                logger.info(f"------ Extracted websites: {website}")
                            else:
                                logger.info(f"---!!! No websites found in {business_data['business_name']}")

            except Exception as e:
                logger.warning(f"Failed to fetch/parse detail page {report_url}: {e}")

        return business_data

    def scrape_city_search_url(self, search_url: str, target_records: Optional[int] = None) -> List[Dict]:
        """
        Scrape a BBB search results page (HTML) for a single city URL, following pagination.

        The BBB search page embeds the results JSON in a window.__PRELOADED_STATE__ JavaScript
        variable. This method requests the HTML for successive pages and extracts that JSON to
        collect business records.

        Args:
            search_url: Full search URL (e.g. the sample Chicago URL)
            target_records: Optional maximum number of business records to collect

        Returns:
            List of normalized business dictionaries
        """
        logger.info(f"Scraping city URL with pagination: {search_url}")

        collected = []
        page = 1

        # Track business names we have already collected for this city to avoid duplicates
        seen_names = set()

        while True:
            if target_records and len(collected) >= target_records:
                break

            params = {"page": page}

            # Respect rate limit before each HTML request
            self._respect_rate_limit()

            success = False
            html = None
            for attempt in range(MAX_RETRIES):
                try:
                    logger.info(f"--- Fetching page {page} for {search_url} (attempt {attempt+1})")
                    resp = self.session.get(search_url, params=params, timeout=REQUEST_TIMEOUT,
                                            proxies=PROXY if PROXY else None)
                    logger.info(f"--- Received status {resp.status_code} for page {page}")
                    if resp.status_code == 200:
                        html = resp.text
                        success = True
                        break
                    elif resp.status_code == 429:
                        logger.warning("--- Rate limited while fetching HTML; backing off")
                        time.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        logger.warning(f"--- Unexpected status {resp.status_code} fetching HTML page")
                except requests.exceptions.RequestException as e:
                    logger.warning(f"--- HTML request failed: {e}")
                    time.sleep(RETRY_DELAY)

            logger.info(f"--- Finished HTML fetch attempts for page {page}")
            if not success or not html:
                logger.error(f"--- Failed to fetch HTML for page {page}: {search_url}")
                break

            # Try to extract the embedded JSON from window.__PRELOADED_STATE__
            data = None
            try:
                marker = 'window.__PRELOADED_STATE__'
                idx = html.find(marker)
                if idx != -1:
                    # Find start of JSON (first '{' after the marker)
                    brace_idx = html.find('{', idx)
                    if brace_idx != -1:
                        # Heuristic: find the script end after the marker and trim to last closing '}' before it
                        script_end = html.find('</script>', brace_idx)
                        snippet = html[brace_idx:script_end] if script_end != -1 else html[brace_idx:]
                        # Find last occurrence of '};' which usually ends the assignment
                        last_obj_end = snippet.rfind('};')
                        if last_obj_end != -1:
                            json_text = snippet[:last_obj_end+1]
                        else:
                            # fallback to regex capture
                            m = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.*?})\s*;', html, re.DOTALL)
                            json_text = m.group(1) if m else None

                        if json_text:
                            data = json.loads(json_text)
                else:
                    # fallback: try regex across whole HTML
                    m = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.*?})\s*;', html, re.DOTALL)
                    if m:
                        data = json.loads(m.group(1))
            except Exception as e:
                logger.warning(f"Failed to parse embedded JSON on page {page}: {e}")

            if not data:
                logger.error(f"No embedded preloaded state found on page {page}")
                break

            search_result = data.get('searchResult') or data.get('page', {}).get('searchResult') or data.get('page', {}).get('searchResult')
            if not search_result:
                # Some pages embed under top-level 'searchResult'
                search_result = data.get('searchResult')

            if not search_result:
                logger.error(f"No searchResult object found on page {page}")
                break

            results = search_result.get('results', [])
            total_pages = search_result.get('totalPages', 1)

            for record in results:
                if target_records and len(collected) >= target_records:
                    break

                if not self.is_valid_businessName(record.get('businessName', '').strip()):
                    self.invalid_records.append(record.get('businessName', 'Unknown'))
                    continue



                # Normalize and clean the business name for deduplication
                raw_name = record.get('businessName') or ''
                name_key = clean_html_tags(raw_name).strip().lower()
                if name_key in seen_names:
                    logger.info(f"---!!! Skipping duplicate business name in city results: {raw_name}")
                    continue
                
                # Check if business already exists in CSV file across all cities
                if name_key in self.existing_business_names:
                    logger.info(f"---!!! Skipping duplicate business (exists in CSV): {raw_name}")
                    continue

                retv = self.extract_business_data(record, source_url=search_url)
                if retv["street_address"] or retv["email"]:
                    seen_names.add(name_key)
                    # Also add to global CSV tracking set to prevent duplicates in subsequent cities
                    self.existing_business_names.add(name_key)
                    collected.append(retv)
                else:
                    logger.info(f"---!!! Excluding Business '{raw_name}' - email or address missing(address: {retv['street_address']}, email: {retv['email']})")

            logger.info(f"Page {page} processed: {len(results)} results, collected total {len(collected)}")

            if page >= total_pages:
                break

            page += 1

        self.valid_records = collected
        logger.info(f"Completed city scrape. Collected {len(collected)} valid records.")
        return collected

