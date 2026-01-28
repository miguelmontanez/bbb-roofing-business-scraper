"""
Main script to loop through all US cities and scrape roofing contractors from BBB.org
Saves all records to CSV and tracks unsupported cities to JSON
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime

from src.scraper import BBBScraper
from src.csv_exporter import CSVExporter
from config import DATA_DIR
from src.utils import setup_logging

# Setup logging
logger = setup_logging()

# File paths
DISPLAY_TEXTS_FILE = Path("assets/display_texts.json")
OUTPUT_CSV = DATA_DIR / "all_cities_records.csv"
UNSUPPORTED_CITIES_JSON = DATA_DIR / "unsupported_cities.json"
SCRAPE_SUMMARY_JSON = DATA_DIR / "scrape_summary.json"


def build_search_url(city: str, state: str) -> str:
    """
    Build a BBB search URL for a given city and state
    
    Args:
        city: City name
        state: State code (2-letter)
        
    Returns:
        Full search URL
    """
    from urllib.parse import quote
    
    location = f"{city}, {state}"
    location_encoded = quote(location)
    
    url = (
        f"https://www.bbb.org/search?"
        f"find_text=Roofing+Contractors&"
        f"find_entity=&"
        f"find_type=&"
        f"find_loc={location_encoded}&"
        f"find_country=USA"
    )
    return url


def load_display_texts() -> List[str]:
    """
    Load city list from display_texts.json
    
    Returns:
        List of "City, State" strings
    """
    if not DISPLAY_TEXTS_FILE.exists():
        logger.error(f"Display texts file not found: {DISPLAY_TEXTS_FILE}")
        return []
    
    try:
        with open(DISPLAY_TEXTS_FILE, "r", encoding="utf-8") as f:
            display_texts = json.load(f)
        logger.info(f"Loaded {len(display_texts)} cities from {DISPLAY_TEXTS_FILE}")
        return display_texts
    except Exception as e:
        logger.error(f"Failed to load display texts: {e}")
        return []


def scrape_all_cities(target_records_per_city: int = None, 
                      max_cities: int = None,
                      skip_cities: int = 0) -> tuple[List[Dict], Set[str]]:
    """
    Loop through all cities and scrape roofing contractors
    
    Args:
        target_records_per_city: Max records to collect per city (None = all)
        max_cities: Max number of cities to process (None = all)
        skip_cities: Number of cities to skip at the beginning
        
    Returns:
        Tuple of (all_records, unsupported_cities_set)
    """
    display_texts = load_display_texts()
    
    if not display_texts:
        logger.error("No cities to scrape")
        return [], set()
    
    if max_cities:
        display_texts = display_texts[:max_cities]
    
    if skip_cities > 0:
        display_texts = display_texts[skip_cities:]
    
    scraper = BBBScraper()
    all_records = []
    unsupported_cities = set()
    
    total_cities = len(display_texts)
    processed_cities = 0
    failed_cities = 0
    
    logger.info(f"Starting to scrape {total_cities} cities")
    logger.info(f"Target records per city: {target_records_per_city or 'all'}")
    
    for idx, display_text in enumerate(display_texts, 1):
        try:
            # Parse city and state
            parts = display_text.rsplit(", ", 1)
            if len(parts) != 2:
                logger.warning(f"Invalid display text format: {display_text}")
                unsupported_cities.add(display_text)
                continue
            
            city, state = parts
            city = city.strip()
            state = state.strip()
            
            logger.info(f"\n[{idx}/{total_cities}] Processing: {city}, {state}")
            
            # Build search URL
            search_url = build_search_url(city, state)
            
            # Scrape this city
            try:
                records = scraper.scrape_city_search_url(
                    search_url, 
                    target_records=target_records_per_city
                )
                
                if records:
                    all_records.extend(records)
                    logger.info(f"✓ Scraped {len(records)} records from {city}, {state}")
                else:
                    logger.warning(f"✗ No records found for {city}, {state}")
                    unsupported_cities.add(display_text)
                    failed_cities += 1
                
                processed_cities += 1
                
            except Exception as e:
                logger.error(f"✗ Error scraping {city}, {state}: {e}")
                unsupported_cities.add(display_text)
                failed_cities += 1
        
        except Exception as e:
            logger.error(f"Error processing city entry '{display_text}': {e}")
            unsupported_cities.add(display_text)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Scraping complete!")
    logger.info(f"  Total records collected: {len(all_records)}")
    logger.info(f"  Cities processed: {processed_cities}/{total_cities}")
    logger.info(f"  Failed/unsupported cities: {len(unsupported_cities)}")
    logger.info(f"{'='*60}\n")
    
    return all_records, unsupported_cities


def save_results(all_records: List[Dict], unsupported_cities: Set[str]) -> bool:
    """
    Save scraping results to CSV and JSON files
    
    Args:
        all_records: List of scraped records
        unsupported_cities: Set of cities where scraping failed
        
    Returns:
        True if successful
    """
    try:
        # Create data directory
        DATA_DIR.mkdir(exist_ok=True)
        
        # Export CSV
        logger.info(f"Exporting {len(all_records)} records to {OUTPUT_CSV}")
        csv_success = CSVExporter.export(all_records, str(OUTPUT_CSV))
        
        if csv_success:
            logger.info(f"✓ CSV export successful")
        else:
            logger.error(f"✗ CSV export failed")
        
        # Validate CSV
        if csv_success:
            is_valid, errors = CSVExporter.validate_csv(str(OUTPUT_CSV))
            if is_valid:
                logger.info("✓ CSV validation passed")
            else:
                logger.warning("✗ CSV validation failed:")
                for error in errors[:5]:  # Show first 5 errors
                    logger.warning(f"  - {error}")
        
        # Export unsupported cities
        unsupported_list = sorted(list(unsupported_cities))
        logger.info(f"Saving {len(unsupported_list)} unsupported cities to {UNSUPPORTED_CITIES_JSON}")
        
        with open(UNSUPPORTED_CITIES_JSON, "w", encoding="utf-8") as f:
            json.dump(unsupported_list, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Unsupported cities saved")
        
        # Save summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_records_collected": len(all_records),
            "total_unsupported_cities": len(unsupported_list),
            "unsupported_cities_file": str(UNSUPPORTED_CITIES_JSON),
            "records_file": str(OUTPUT_CSV)
        }
        
        logger.info(f"Saving summary to {SCRAPE_SUMMARY_JSON}")
        with open(SCRAPE_SUMMARY_JSON, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"✓ Summary saved")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scrape roofing contractors from BBB.org for all US cities"
    )
    parser.add_argument(
        "--max-cities",
        type=int,
        default=None,
        help="Maximum number of cities to process"
    )
    parser.add_argument(
        "--records-per-city",
        type=int,
        default=None,
        help="Maximum records to collect per city"
    )
    parser.add_argument(
        "--skip-cities",
        type=int,
        default=0,
        help="Number of cities to skip at the beginning"
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("BBB Roofing Contractors - All Cities Scraper")
    logger.info("="*60)
    logger.info(f"Options:")
    logger.info(f"  Max cities: {args.max_cities or 'all'}")
    logger.info(f"  Records per city: {args.records_per_city or 'all'}")
    logger.info(f"  Skip first: {args.skip_cities} cities")
    logger.info("="*60)
    
    # Scrape all cities
    all_records, unsupported_cities = scrape_all_cities(
        target_records_per_city=args.records_per_city,
        max_cities=args.max_cities,
        skip_cities=args.skip_cities
    )
    
    # Save results
    success = save_results(all_records, unsupported_cities)
    
    if success:
        logger.info("\n✓ All operations completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n✗ Some operations failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
