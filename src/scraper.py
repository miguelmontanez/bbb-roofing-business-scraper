"""
Main scraper class for collecting BBB roofing contractor data
"""

import logging
import time
import json
import re
from typing import List, Dict, Optional
import requests
from urllib.parse import urlencode

from config import (
    BBB_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY,
    RECORDS_PER_PAGE, KEYWORD_FILTERS, LOWER_48_STATES, USER_AGENT,
    RATE_LIMIT, PROXY
)
from src.utils import contains_keyword, normalize_state, setup_logging, clean_html_tags

logger = logging.getLogger("bbb_scraper")


class BBBScraper:
    """Web scraper for BBB.org roofing contractor data"""
    
    def __init__(self):
        """Initialize the scraper"""
        self.base_url = BBB_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.last_request_time = 0
        self.valid_records = []
        self.invalid_records = []
        
    def _respect_rate_limit(self):
        """Implement rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < (1 / RATE_LIMIT):
            time.sleep((1 / RATE_LIMIT) - elapsed)
        self.last_request_time = time.time()
    
    def is_valid_record(self, record: Dict) -> bool:
        """
        Validate if a business record meets inclusion criteria
        
        Args:
            record: Business record from BBB
            
        Returns:
            True if record meets all criteria
        """
        # Check business name contains required keyword
        business_name = (record.get("businessName") or "").strip()
        if not contains_keyword(business_name, KEYWORD_FILTERS):
            logger.info(f"---!!! Excluding Business Name '{business_name}' - does not match keywords")
            return False
        
        # Check state is in lower 48
        state = (record.get("state") or "").strip()
        if state not in LOWER_48_STATES:
            logger.info(f"---!!! Excluding State '{state}' - state {state} not in lower 48")
            return False
        
        # Check address exists
        address = (record.get("address") or "").strip()
        if not address or len(address) < 3:
            logger.info(f"---!!! Excluding Address '{address}' - invalid address")
            return False
        
        # Check city exists
        city = (record.get("city") or "").strip()
        if not city or len(city) < 2:
            logger.info(f"---!!! Excluding City '{city}' - invalid city")
            return False
        
        # Check postal code exists
        postal = (record.get("postalcode") or "").strip()
        if not postal:
            logger.info(f"---!!! Excluding Postal Code '{postal}' - missing postal code")
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
            "rating": (record.get("rating") or ""),
            "bbb_member": str(record.get("bbbMember", False)).lower(),
            "bbb_accredited": str(record.get("accreditedCharity", False)).lower(),
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
                    try:
                        # Prefer schema.org JSON-LD if present (contains reliable employee info)
                        m2 = re.search(r'<script type="application/ld\+json">(.*?)</script>', detail_html, re.DOTALL)
                        schema_ld = None
                        if m2:
                            try:
                                schema_ld = json.loads(m2.group(1))
                            except Exception:
                                schema_ld = None

                        # Fallback to window.__PRELOADED_STATE__ if no JSON-LD
                        if schema_ld is not None:
                            detail_data = schema_ld
                        else:
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

                    if detail_data:
                        # Dates
                        dates = find_key(detail_data, "dates") or {}
                        if isinstance(dates, dict):
                            business_data["incorporated_date"] = dates.get("incorporated") or business_data["incorporated_date"]
                            business_data["business_started"] = dates.get("businessStart") or business_data["business_started"]

                        # Entity type
                        type_of_entity = find_key(detail_data, "typeOfEntity") or {}
                        if isinstance(type_of_entity, dict):
                            business_data["entity_type"] = type_of_entity.get("name") or business_data["entity_type"]

                        # Principal contact(s) - Extract from contactInformation
                        contacts = []
                        contact_info = find_key(detail_data, "contactInformation")
                        
                        if contact_info and isinstance(contact_info, dict):
                            # Look for principal contact in contacts array
                            contacts_list = contact_info.get("contacts", [])
                            if isinstance(contacts_list, list):
                                for contact in contacts_list:
                                    if isinstance(contact, dict) and contact.get("isPrincipal"):
                                        # Extract name components
                                        name_obj = contact.get("name", {})
                                        if isinstance(name_obj, dict):
                                            first = (name_obj.get("first") or "").strip()
                                            middle = (name_obj.get("middle") or "").strip()
                                            last = (name_obj.get("last") or "").strip()
                                            
                                            # Build full name: first middle last
                                            full_name_parts = [first, middle, last]
                                            full_name = " ".join([p for p in full_name_parts if p])
                                            
                                            if full_name:
                                                contacts.append(full_name)
                                            break  # Only take the first principal contact

                        if contacts:
                            business_data["principal_contact"] = "; ".join(contacts)

                        # Referral assistance texts may contain website (do not override phone)
                        ref_texts = find_key(detail_data, "referralAssistanceTexts") or []
                        if isinstance(ref_texts, list):
                            for txt in ref_texts:
                                if not isinstance(txt, str):
                                    continue
                                # URL
                                murl = re.search(r'(https?://[\w\-._~:/?#\[\]@!$&'""'()*+,;=%]+)', txt)
                                if murl:
                                    business_data["website"] = business_data.get("website") or murl.group(1).strip()

                        # Also check schema.org telephone if phone not present (but prefer main page phone)
                        if not business_data.get("phone"):
                            tel = find_key(detail_data, "telephone")
                            if tel:
                                business_data["phone"] = tel.strip()

                        # Extract email from contactInformation (primary source)
                        if contact_info and isinstance(contact_info, dict):
                            email = (contact_info.get("emailAddress") or "").strip()
                            if email:
                                business_data["email"] = email
                                logger.info(f"Extracted email from contactInformation: {email}")

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
                    logger.info(f"Fetching page {page} for {search_url} (attempt {attempt+1})")
                    resp = self.session.get(search_url, params=params, timeout=REQUEST_TIMEOUT,
                                            proxies=PROXY if PROXY else None)
                    logger.info(f"Received status {resp.status_code} for page {page}")
                    if resp.status_code == 200:
                        html = resp.text
                        success = True
                        break
                    elif resp.status_code == 429:
                        logger.warning("Rate limited while fetching HTML; backing off")
                        time.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        logger.warning(f"Unexpected status {resp.status_code} fetching HTML page")
                except requests.exceptions.RequestException as e:
                    logger.warning(f"HTML request failed: {e}")
                    time.sleep(RETRY_DELAY)

            logger.info(f"Finished HTML fetch attempts for page {page}")
            if not success or not html:
                logger.error(f"Failed to fetch HTML for page {page}: {search_url}")
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

                if not self.is_valid_record(record):
                    self.invalid_records.append(record.get('businessName', 'Unknown'))
                    continue

                # Normalize and clean the business name for deduplication
                raw_name = record.get('businessName') or ''
                name_key = clean_html_tags(raw_name).strip().lower()
                if name_key in seen_names:
                    logger.info(f"Skipping duplicate business name in city results: {raw_name}")
                    continue

                seen_names.add(name_key)
                collected.append(self.extract_business_data(record, source_url=search_url))

            logger.info(f"Page {page} processed: {len(results)} results, collected total {len(collected)}")

            if page >= total_pages:
                break

            page += 1

        self.valid_records = collected
        logger.info(f"Completed city scrape. Collected {len(collected)} valid records.")
        return collected

