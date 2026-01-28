"""
Main entry point for BBB Roofing Contractor Scraper
"""

import logging
import argparse
from pathlib import Path
from typing import Optional

from config import DATA_DIR
from src.utils import setup_logging
from src.scraper import BBBScraper
from src.data_processor import DataProcessor
from src.csv_exporter import CSVExporter

# Setup logging
logger = setup_logging()


def run_scrape(target_records: int, output_file: Optional[str] = None) -> bool:
    """Run a single scrape session for the requested number of records.

    Args:
        target_records: Number of records to collect
        output_file: Optional output CSV path

    Returns:
        True on success
    """
    output_path = Path(output_file) if output_file else (DATA_DIR / "records.csv")

    logger.info("=" * 60)
    logger.info(f"SCRAPE: Target {target_records} records")
    logger.info("=" * 60)

    try:
        scraper = BBBScraper()

        logger.info(f"Starting scrape for {target_records} records...")
        raw_records = scraper.scrape_phase_1(target_records=target_records)

        stats = scraper.get_statistics()
        logger.info(f"Scraper Statistics: {stats}")

        if not raw_records:
            logger.error("No records collected during scraping")
            return False

        logger.info("Processing and validating records...")
        processor = DataProcessor()
        cleaned_records = processor.process_records(raw_records)

        unique_records = processor.remove_duplicates(cleaned_records)

        logger.info(f"Final record count: {len(unique_records)}")
        processor_stats = processor.get_statistics()
        logger.info(f"Processor Statistics: {processor_stats}")

        logger.info(f"Exporting to CSV: {output_path}")
        success = CSVExporter.export(unique_records, str(output_path))

        if success:
            is_valid, errors = CSVExporter.validate_csv(str(output_path))

            if is_valid:
                file_stats = CSVExporter.get_file_stats(str(output_path))
                logger.info(f"CSV Statistics: {file_stats}")
                logger.info("Scrape COMPLETED SUCCESSFULLY")
                return True
            else:
                logger.error(f"CSV validation failed: {errors}")
                return False
        else:
            logger.error("Failed to export CSV")
            return False

    except Exception as e:
        logger.error(f"Scrape failed with error: {str(e)}", exc_info=True)
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="BBB Roofing Contractor Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --records 300                 # Collect 300 records (test)
  python main.py --records 3000 --output data/all_records.csv  # Collect 3000 records
        """
    )

    parser.add_argument(
        "--records",
        type=int,
        required=True,
        help="Number of records to collect"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output CSV file path (optional)"
    )

    args = parser.parse_args()

    success = run_scrape(target_records=args.records, output_file=args.output)
    
    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
