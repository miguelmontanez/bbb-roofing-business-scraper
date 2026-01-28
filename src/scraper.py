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
from src.utils import contains_keyword, normalize_state, setup_logging

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
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request with retry logic
        
        Args:
            url: Request URL
            params: Query parameters
            
        Returns:
            JSON response or None on failure
        """
        self._respect_rate_limit()
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Request attempt {attempt + 1}/{MAX_RETRIES}: {url}")
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                    proxies=PROXY if PROXY else None
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited
                    logger.warning("Rate limited by BBB.org, waiting...")
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    logger.warning(f"HTTP {response.status_code}: {response.reason}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
        
        logger.error(f"Failed to fetch after {MAX_RETRIES} attempts: {url}")
        return None
    
    def search_businesses(self, location: str, category: str = "Roofing", 
                         page: int = 1) -> Optional[Dict]:
        """
        Search for businesses on BBB.org
        
        Args:
            location: City, State or ZIP code
            category: Business category
            page: Page number
            
        Returns:
            Search results or None
        """
        url = f"{self.base_url}/localservice"
        
        params = {
            "location": location,
            "category": category,
            "pageNumber": page
        }
        
        logger.info(f"Searching: {location}, {category}, Page {page}")
        
        response = self._make_request(url, params)
        
        if response and "searchResult" in response:
            return response["searchResult"]
        
        return None
    
    def is_valid_record(self, record: Dict) -> bool:
        """
        Validate if a business record meets inclusion criteria
        
        Args:
            record: Business record from BBB
            
        Returns:
            True if record meets all criteria
        """
        # Check business name contains required keyword
        business_name = record.get("businessName", "")
        if not contains_keyword(business_name, KEYWORD_FILTERS):
            return False
        
        # Check state is in lower 48
        state = record.get("state", "")
        if state not in LOWER_48_STATES:
            return False
        
        # Check address exists
        address = record.get("address", "").strip()
        if not address or len(address) < 3:
            return False
        
        # Check city exists
        city = record.get("city", "").strip()
        if not city or len(city) < 2:
            return False
        
        # Check postal code exists
        postal = record.get("postalcode", "").strip()
        if not postal:
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
        phones = record.get("phone", [])
        phone = phones[0] if isinstance(phones, list) and phones else ""
        
        # Extract categories
        categories = record.get("categories", [])
        category_names = [cat.get("name", "") for cat in categories]
        categories_str = "; ".join(category_names) if category_names else ""
        
        # Build source URL
        report_url = record.get("reportUrl", "")
        if report_url and not report_url.startswith("http"):
            report_url = f"https://www.bbb.org{report_url}"
        
        business_data = {
            "business_name": record.get("businessName", "").strip(),
            "street_address": record.get("address", "").strip(),
            "city": record.get("city", "").strip(),
            "state": record.get("state", "").strip().upper(),
            "postal_code": record.get("postalcode", "").strip(),
            "phone": phone.strip() if phone else "",
            "email": "",  # BBB doesn't typically provide email in search results
            "website": "",  # Usually not in search results
            "entity_type": "",  # Not available in search results
            "business_started": "",  # Not available in search results
            "incorporated_date": "",  # Not available in search results
            "principal_contact": "",  # Not available in search results
            "business_categories": categories_str,
            "rating": record.get("rating", ""),
            "bbb_member": str(record.get("bbbMember", False)).lower(),
            "bbb_accredited": str(record.get("accreditedCharity", False)).lower(),
            "source_url": report_url
        }
        
        return business_data
    
    def scrape_phase_1(self, target_records: int = 300) -> List[Dict]:
        """
        Scrape Phase 1 data (test scrape)
        
        Args:
            target_records: Number of records to collect
            
        Returns:
            List of business records
        """
        logger.info(f"Starting Phase 1 scrape - Target: {target_records} records")
        
        # Sample locations to search
        locations = [
            "California, CA",
            "Texas, TX", 
            "Florida, FL",
            "New York, NY",
            "Pennsylvania, PA"
        ]
        
        records_collected = 0
        all_records = []
        
        for location in locations:
            if records_collected >= target_records:
                break
            
            page = 1
            while records_collected < target_records:
                results = self.search_businesses(location, page=page)
                
                if not results or not results.get("results"):
                    break
                
                for record in results["results"]:
                    if records_collected >= target_records:
                        break
                    
                    if self.is_valid_record(record):
                        business_data = self.extract_business_data(record)
                        all_records.append(business_data)
                        records_collected += 1
                        logger.info(f"Collected record {records_collected}: {business_data['business_name']}")
                    else:
                        self.invalid_records.append(record.get("businessName", "Unknown"))
                
                # Check if there are more pages
                total_pages = results.get("totalPages", 1)
                if page >= total_pages:
                    break
                
                page += 1
        
        self.valid_records = all_records
        logger.info(f"Phase 1 complete. Collected {len(all_records)} valid records.")
        
        return all_records

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
                    logger.info(f"Received status {resp.text} for page {page}")
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

                if self.is_valid_record(record):
                    collected.append(self.extract_business_data(record, source_url=search_url))
                else:
                    self.invalid_records.append(record.get('businessName', 'Unknown'))

            logger.info(f"Page {page} processed: {len(results)} results, collected total {len(collected)}")

            if page >= total_pages:
                break

            page += 1

        self.valid_records = collected
        logger.info(f"Completed city scrape. Collected {len(collected)} valid records.")
        return collected
    
    def get_statistics(self) -> Dict:
        """
        Get scraping statistics
        
        Returns:
            Dictionary of statistics
        """
        return {
            "valid_records": len(self.valid_records),
            "invalid_records": len(self.invalid_records),
            "total_processed": len(self.valid_records) + len(self.invalid_records)
        }
