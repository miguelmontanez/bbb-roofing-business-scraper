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
SCRAPE_SUMMARY_JSON = DATA_DIR / "scrape_summary.json"
PROGRESS_TRACKING_JSON = DATA_DIR / "scrape_progress.json"


def generate_csv_filename(records_limit: int = None, 
                         start_index: int = None,
                         end_index: int = None,
                         resume_mode: bool = False) -> Path:
    """
    Generate output CSV filename based on command arguments.
    Filenames include argument context to support multi-processing.
    
    Examples:
      all_cities_records.csv (default)
      all_cities_records_r200.csv (records limit 200)
      all_cities_records_i1-100.csv (start index 1 to 100)
      all_cities_records_i1-100_r200.csv (combined)
      all_cities_records_resume.csv (resume mode)
    
    Args:
        records_limit: Total record limit (--records)
        start_index: Start city index (--start-index)
        end_index: End city index (--end-index)
        resume_mode: Whether in resume/pause mode
        
    Returns:
        Path object for output CSV
    """
    filename = "all_cities_records"
    
    if resume_mode:
        filename += "_resume"
    elif start_index is not None or end_index is not None:
        start_str = start_index if start_index else ""
        end_str = end_index if end_index else ""
        filename += f"_i{start_str}-{end_str}"
    
    if records_limit:
        filename += f"_r{records_limit}"
    
    filename += ".csv"
    return DATA_DIR / filename


def backup_existing_csvs() -> None:
    """
    Backup all existing CSV files in data/ directory.
    Appends current date to filenames to preserve previous runs.
    
    Example: all_cities_records.csv -> all_cities_records_2026-01-29.csv
    """
    if not DATA_DIR.exists():
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    csv_files = list(DATA_DIR.glob("*.csv"))
    
    if not csv_files:
        logger.info(f"[INFO] No existing CSV files to backup")
        return
    
    logger.info(f"[ACTION] Backing up {len(csv_files)} existing CSV file(s)")
    for csv_path in csv_files:
        backup_name = csv_path.stem + f"_{today}" + csv_path.suffix
        backup_path = csv_path.parent / backup_name
        try:
            csv_path.rename(backup_path)
            logger.info(f"[SUCCESS] Backed up: {csv_path.name} -> {backup_name}")
        except Exception as e:
            logger.warning(f"[WARNING] Failed to backup {csv_path.name}: {e}")


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
            logger.info("[SUCCESS] Progress file cleared")
        return True
    except Exception as e:
        logger.error(f"Failed to clear progress: {e}")
        return False


def save_record_incremental(record: Dict, csv_path: Path) -> bool:
    """
    Save a single record to CSV incrementally (append mode)
    
    Args:
        record: Business record to save
        csv_path: Path to output CSV file
        
    Returns:
        True if successful
    """
    try:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists (to know if we need header)
        file_exists = csv_path.exists() and csv_path.stat().st_size > 0
        
        with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
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
                      resume_from_progress: bool = False,
                      start_index: int = None,
                      end_index: int = None,
                      csv_path: Path = None) -> bool:
    """
    Loop through all cities and scrape roofing contractors
    Saves records incrementally to CSV after each city.
    
    Args:
        target_records_per_city: Max records to collect per city (None = all)
        max_cities: Max number of cities to process (None = all)
        skip_cities: Number of cities to skip at the beginning
        total_record_limit: Total record limit for entire scrape (None = no limit)
        resume_from_progress: Whether to resume from last processed city
        start_index: Start city index (1-based, inclusive)
        end_index: End city index (1-based, inclusive)
        csv_path: Path to output CSV file
        
    Returns:
        True if successful
    """
    if csv_path is None:
        csv_path = generate_csv_filename(total_record_limit, start_index, end_index, resume_from_progress)
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
    
    # Apply optional start/end index slicing (1-based, inclusive end)
    if start_index is not None or end_index is not None:
        # Convert start to 0-based index
        start = (start_index - 1) if start_index and start_index > 0 else 0
        end = end_index if end_index and end_index > 0 else None
        display_texts = display_texts[start:end]
    else:
        # Filter by skip and max if no explicit start/end provided
        if max_cities:
            display_texts = display_texts[:max_cities]
        
        if skip_cities > 0:
            display_texts = display_texts[skip_cities:]
    
    # Remove already processed cities
    remaining_cities = [c for c in display_texts if c not in processed_cities_set]
    
    total_cities = len(display_texts)
    processed_cities = len(processed_cities_set)
    records_processed_this_run = 0
    
    logger.info(f"\n=== SCRAPE STARTED ===")
    logger.info(f"Total cities available: {total_cities}")
    logger.info(f"Cities to process this run: {len(remaining_cities)}")
    logger.info(f"Records per city limit: {target_records_per_city or 'UNLIMITED'}")
    logger.info(f"Total records limit: {total_record_limit or 'UNLIMITED'}")
    logger.info(f"=== START SCRAPING ===")
    
    for idx, display_text in enumerate(remaining_cities, 1):
        # Check if record limit reached
        if total_record_limit and total_records_so_far >= total_record_limit:
            logger.info(f"[LIMIT-REACHED] Record limit reached: {total_records_so_far}/{total_record_limit}")
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
                        logger.info(f"[INFO] Limiting records to {len(records_to_save)} (from {len(records)})")
                
                # Save each record incrementally
                if records_to_save:
                    saved_count = 0
                    for record in records_to_save:
                        if save_record_incremental(record, csv_path):
                            saved_count += 1
                            total_records_so_far += 1
                            records_processed_this_run += 1
                        else:
                            logger.warning(f"[ERROR] Failed to save record for {city}, {state}")
                    
                    logger.info(f"[SUCCESS] City {city},{state}: Saved {saved_count} records (Total: {total_records_so_far})")
                else:
                    logger.info(f"[NO-RESULTS] City {city},{state}: No contractors found")
                
                processed_cities += 1
                
            except Exception as e:
                logger.error(f"[ERROR] Exception scraping {city},{state}: {str(e)}")
        
        except Exception as e:
            logger.error(f"[ERROR] Invalid city entry '{display_text}': {str(e)}")
        
        # Save progress after each city
        progress["processed_cities"] = list(processed_cities_set | {display_text})
        progress["total_records"] = total_records_so_far
        progress["timestamp_last_update"] = datetime.now().isoformat()
        save_progress(progress)
    
    logger.info(f"\n=== SCRAPE SESSION COMPLETE ===")
    logger.info(f"Session Records Collected: {records_processed_this_run}")
    logger.info(f"Total Records (All-Time): {total_records_so_far}")
    logger.info(f"Cities Processed This Run: {processed_cities - len(processed_cities_set)}/{len(remaining_cities)}")
    logger.info(f"Total Cities Processed Ever: {processed_cities}/{total_cities}")
    logger.info(f"Output CSV: {csv_path}")
    logger.info(f"Progress File: {PROGRESS_TRACKING_JSON}")
    logger.info(f"=== END OF SESSION ===\n")
    
    return True


def save_final_summary(total_records: int, csv_path: Path) -> bool:
    """
    Save final summary statistics
    
    Args:
        total_records: Total records collected
        csv_path: Path to output CSV file
        
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
            "records_file": str(csv_path)
        }
        
        logger.info(f"Saving summary to {SCRAPE_SUMMARY_JSON}")
        with open(SCRAPE_SUMMARY_JSON, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"[SUCCESS] Summary saved")
        
        # Validate CSV
        if csv_path.exists():
            is_valid, errors = CSVExporter.validate_csv(str(csv_path))
            if is_valid:
                logger.info("[SUCCESS] CSV validation passed")
            else:
                logger.warning("[WARNING] CSV validation found issues:")
                for error in errors[:5]:
                    logger.warning(f"  - {error}")
        
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to save summary: {e}")
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
    parser.add_argument(
        "--start-index",
        type=int,
        default=None,
        help="Start index for cities (1-based, inclusive)"
    )
    parser.add_argument(
        "--end-index",
        type=int,
        default=None,
        help="End index for cities (1-based, inclusive)"
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("BBB Roofing Contractors - All Cities Scraper")
    logger.info("="*60)
    
    # Generate output CSV filename based on arguments
    output_csv = generate_csv_filename(args.records, args.start_index, args.end_index, args.pause)
    logger.info(f"[CONFIG] Output CSV: {output_csv.name}")
    
    # Backup existing CSVs before starting
    backup_existing_csvs()
    
    # Handle --reset
    if args.reset:
        logger.info("[ACTION] Clearing progress file (--reset)")
        clear_progress()
        logger.info("[INFO] Starting fresh from first city...")
    
    logger.info(f"Options:")
    logger.info(f"  Max cities: {args.max_cities or 'no limit'}")
    logger.info(f"  Total record limit: {args.records or 'no limit'}")
    logger.info(f"  Records per city: {args.records_per_city or 'all'}")
    logger.info(f"  Skip first: {args.skip_cities} cities")
    logger.info(f"  Resume from progress: {args.pause}")
    logger.info(f"  Start index: {args.start_index or 'none'}")
    logger.info(f"  End index: {args.end_index or 'none'}")
    logger.info("="*60)
    
    # Scrape all cities with new parameters
    success = scrape_all_cities(
        target_records_per_city=args.records_per_city,
        max_cities=args.max_cities,
        skip_cities=args.skip_cities,
        total_record_limit=args.records,
        resume_from_progress=args.pause,
        start_index=args.start_index,
        end_index=args.end_index,
        csv_path=output_csv
    )
    
    # Save final summary
    if success:
        progress = load_progress()
        total_records = progress.get("total_records", 0)
        save_final_summary(total_records, output_csv)
        
        logger.info("\n[SUCCESS] All operations completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n[ERROR] Scraping failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
