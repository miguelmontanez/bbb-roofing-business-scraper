"""
Main script to loop through all US cities and scrape roofing contractors from BBB.org
Saves records incrementally after each city for resume capability.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
import csv

from src.scraper import BBBScraper
from src.csv_exporter import CSVExporter
from config import DATA_DIR, CSV_COLUMNS
from src.utils import setup_logging

# Setup logging
logger = setup_logging()

# File paths
DISPLAY_TEXTS_FILE = Path("assets/display_texts.json")
OUTPUT_CSV = DATA_DIR / "all_cities_records.csv"
SCRAPE_SUMMARY_JSON = DATA_DIR / "scrape_summary.json"
PROGRESS_TRACKING_JSON = DATA_DIR / "scrape_progress.json"


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


def load_progress() -> Dict:
    """
    Load scraping progress from tracking file
    
    Returns:
        Dictionary with processed cities and record count
    """
    if not PROGRESS_TRACKING_JSON.exists():
        return {
            "processed_cities": [],
            "total_records": 0,
            "timestamp_started": datetime.now().isoformat()
        }
    
    try:
        with open(PROGRESS_TRACKING_JSON, "r", encoding="utf-8") as f:
            progress = json.load(f)
        logger.info(f"Loaded progress: {len(progress.get('processed_cities', []))} cities processed")
        return progress
    except Exception as e:
        logger.warning(f"Could not load progress file: {e}")
        return {
            "processed_cities": [],
            "total_records": 0,
            "timestamp_started": datetime.now().isoformat()
        }


def save_progress(progress: Dict) -> bool:
    """
    Save scraping progress to tracking file
    
    Args:
        progress: Progress dictionary
        
    Returns:
        True if successful
    """
    try:
        DATA_DIR.mkdir(exist_ok=True)
        with open(PROGRESS_TRACKING_JSON, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save progress: {e}")
        return False


def clear_progress() -> bool:
    """
    Clear progress tracking file (for --reset)
    
    Returns:
        True if successful
    """
    try:
        if PROGRESS_TRACKING_JSON.exists():
            PROGRESS_TRACKING_JSON.unlink()
            logger.info("✓ Progress file cleared")
        return True
    except Exception as e:
        logger.error(f"Failed to clear progress: {e}")
        return False


def save_record_incremental(record: Dict) -> bool:
    """
    Save a single record to CSV incrementally (append mode)
    
    Args:
        record: Business record to save
        
    Returns:
        True if successful
    """
    try:
        DATA_DIR.mkdir(exist_ok=True)
        
        # Check if file exists (to know if we need header)
        file_exists = OUTPUT_CSV.exists() and OUTPUT_CSV.stat().st_size > 0
        
        with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS, restval="")
            
            # Write header only if file is new
            if not file_exists:
                writer.writeheader()
            
            # Ensure all required columns are present
            row = {col: record.get(col, "") for col in CSV_COLUMNS}
            writer.writerow(row)
        
        return True
    except Exception as e:
        logger.error(f"Failed to save record incrementally: {e}")
        return False


def scrape_all_cities(target_records_per_city: int = None, 
                      max_cities: int = None,
                      skip_cities: int = 0,
                      total_record_limit: int = None,
                      resume_from_progress: bool = False) -> bool:
    """
    Loop through all cities and scrape roofing contractors
    Saves records incrementally to CSV after each city.
    
    Args:
        target_records_per_city: Max records to collect per city (None = all)
        max_cities: Max number of cities to process (None = all)
        skip_cities: Number of cities to skip at the beginning
        total_record_limit: Total record limit for entire scrape (None = no limit)
        resume_from_progress: Whether to resume from last processed city
        
    Returns:
        True if successful
    """
    display_texts = load_display_texts()
    
    if not display_texts:
        logger.error("No cities to scrape")
        return False
    
    # Load progress if resuming
    progress = {}
    processed_cities_set = set()
    if resume_from_progress:
        progress = load_progress()
        processed_cities_set = set(progress.get("processed_cities", []))
        total_records_so_far = progress.get("total_records", 0)
        logger.info(f"Resuming from last session: {len(processed_cities_set)} cities already processed")
        logger.info(f"Records already collected: {total_records_so_far}")
    else:
        progress = {
            "processed_cities": [],
            "total_records": 0,
            "timestamp_started": datetime.now().isoformat(),
            "total_record_limit": total_record_limit
        }
        total_records_so_far = 0
    
    scraper = BBBScraper()
    
    # Filter cities
    if max_cities:
        display_texts = display_texts[:max_cities]
    
    if skip_cities > 0:
        display_texts = display_texts[skip_cities:]
    
    # Remove already processed cities
    remaining_cities = [c for c in display_texts if c not in processed_cities_set]
    
    total_cities = len(display_texts)
    processed_cities = len(processed_cities_set)
    records_processed_this_run = 0
    
    logger.info(f"Starting scrape - Total cities: {total_cities}")
    logger.info(f"Cities to process: {len(remaining_cities)}")
    logger.info(f"Target records per city: {target_records_per_city or 'all'}")
    logger.info(f"Total record limit: {total_record_limit or 'no limit'}")
    
    for idx, display_text in enumerate(remaining_cities, 1):
        # Check if record limit reached
        if total_record_limit and total_records_so_far >= total_record_limit:
            logger.info(f"✓ Record limit reached ({total_records_so_far}/{total_record_limit})")
            break
        
        try:
            # Parse city and state
            parts = display_text.rsplit(", ", 1)
            if len(parts) != 2:
                logger.warning(f"Invalid display text format: {display_text}")
                continue
            
            city, state = parts
            city = city.strip()
            state = state.strip()
            
            current_position = processed_cities + idx
            logger.info(f"\n[{current_position}/{total_cities}] Processing: {city}, {state}")
            
            # Build search URL
            search_url = build_search_url(city, state)
            
            # Scrape this city
            try:
                records = scraper.scrape_city_search_url(
                    search_url, 
                    target_records=target_records_per_city
                )
                
                # Calculate how many records we can save (respecting limit)
                records_to_save = records
                if total_record_limit:
                    remaining_quota = total_record_limit - total_records_so_far
                    if len(records) > remaining_quota:
                        records_to_save = records[:remaining_quota]
                        logger.info(f"⚠ Truncating records to respect limit ({len(records)} -> {len(records_to_save)})")
                
                # Save each record incrementally
                if records_to_save:
                    saved_count = 0
                    for record in records_to_save:
                        if save_record_incremental(record):
                            saved_count += 1
                            total_records_so_far += 1
                            records_processed_this_run += 1
                        else:
                            logger.warning(f"Failed to save record for {city}, {state}")
                    
                    logger.info(f"✓ Saved {saved_count} records from {city}, {state}")
                else:
                    logger.warning(f"✗ No records found for {city}, {state}")
                
                processed_cities += 1
                
            except Exception as e:
                logger.error(f"✗ Error scraping {city}, {state}: {e}")
        
        except Exception as e:
            logger.error(f"Error processing city entry '{display_text}': {e}")
        
        # Save progress after each city
        progress["processed_cities"] = list(processed_cities_set | {display_text})
        progress["total_records"] = total_records_so_far
        progress["timestamp_last_update"] = datetime.now().isoformat()
        save_progress(progress)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Scraping session complete!")
    logger.info(f"  Records collected this session: {records_processed_this_run}")
    logger.info(f"  Total records collected (all time): {total_records_so_far}")
    logger.info(f"  Cities processed: {processed_cities}/{total_cities}")
    logger.info(f"  CSV saved to: {OUTPUT_CSV}")
    logger.info(f"  Progress saved to: {PROGRESS_TRACKING_JSON}")
    logger.info(f"{'='*60}\n")
    
    return True


def save_final_summary(total_records: int) -> bool:
    """
    Save final summary statistics
    
    Args:
        total_records: Total records collected
        
    Returns:
        True if successful
    """
    try:
        DATA_DIR.mkdir(exist_ok=True)
        
        # Read current progress to get all processed cities
        progress = load_progress()
        
        # Save summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_records_collected": total_records,
            "total_cities_processed": len(progress.get("processed_cities", [])),
            "progress_file": str(PROGRESS_TRACKING_JSON),
            "records_file": str(OUTPUT_CSV)
        }
        
        logger.info(f"Saving summary to {SCRAPE_SUMMARY_JSON}")
        with open(SCRAPE_SUMMARY_JSON, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"✓ Summary saved")
        
        # Validate CSV
        if OUTPUT_CSV.exists():
            is_valid, errors = CSVExporter.validate_csv(str(OUTPUT_CSV))
            if is_valid:
                logger.info("✓ CSV validation passed")
            else:
                logger.warning("✗ CSV validation found issues:")
                for error in errors[:5]:
                    logger.warning(f"  - {error}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save summary: {e}")
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scrape roofing contractors from BBB.org for all US cities with resume capability"
    )
    parser.add_argument(
        "--max-cities",
        type=int,
        default=None,
        help="Maximum number of cities to process in this run"
    )
    parser.add_argument(
        "--records",
        type=int,
        default=None,
        help="Total record limit (stops scraping when reached)"
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
    parser.add_argument(
        "--pause",
        action="store_true",
        help="Resume from last processed city (uses progress tracking)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear previous progress and start from the first city"
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("BBB Roofing Contractors - All Cities Scraper")
    logger.info("="*60)
    
    # Handle --reset
    if args.reset:
        logger.info("Clearing progress file (--reset)")
        clear_progress()
        if OUTPUT_CSV.exists():
            OUTPUT_CSV.unlink()
            logger.info("✓ Cleared previous CSV file")
        logger.info("Starting fresh from first city...")
    
    logger.info(f"Options:")
    logger.info(f"  Max cities: {args.max_cities or 'no limit'}")
    logger.info(f"  Total record limit: {args.records or 'no limit'}")
    logger.info(f"  Records per city: {args.records_per_city or 'all'}")
    logger.info(f"  Skip first: {args.skip_cities} cities")
    logger.info(f"  Resume from progress: {args.pause}")
    logger.info("="*60)
    
    # Scrape all cities with new parameters
    success = scrape_all_cities(
        target_records_per_city=args.records_per_city,
        max_cities=args.max_cities,
        skip_cities=args.skip_cities,
        total_record_limit=args.records,
        resume_from_progress=args.pause
    )
    
    # Save final summary
    if success:
        progress = load_progress()
        total_records = progress.get("total_records", 0)
        save_final_summary(total_records)
        
        logger.info("\n✓ All operations completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n✗ Scraping failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
