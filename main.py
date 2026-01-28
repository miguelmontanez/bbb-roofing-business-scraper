"""
Main entry point for BBB Roofing Contractor Scraper
"""

import logging
import argparse
from pathlib import Path
from typing import Optional

from config import PHASE_1_OUTPUT, PHASE_2_OUTPUT, PHASE_1_RECORDS, PHASE_2_RECORDS
from src.utils import setup_logging
from src.scraper import BBBScraper
from src.data_processor import DataProcessor
from src.csv_exporter import CSVExporter

# Setup logging
logger = setup_logging()


def scrape_phase_1(output_file: Optional[str] = None) -> bool:
    """
    Execute Phase 1 scraping (test phase - 300 records)
    
    Args:
        output_file: Custom output file path
        
    Returns:
        True if successful
    """
    output_path = Path(output_file) if output_file else PHASE_1_OUTPUT
    
    logger.info("="*60)
    logger.info("PHASE 1: Test Scrape (300 records)")
    logger.info("="*60)
    
    try:
        # Initialize scraper
        scraper = BBBScraper()
        
        # Scrape data
        logger.info("Starting Phase 1 scrape...")
        raw_records = scraper.scrape_phase_1(target_records=PHASE_1_RECORDS)
        
        # Log statistics
        stats = scraper.get_statistics()
        logger.info(f"Scraper Statistics: {stats}")
        
        if not raw_records:
            logger.error("No records collected during scraping")
            return False
        
        # Process and validate data
        logger.info("Processing and validating records...")
        processor = DataProcessor()
        cleaned_records = processor.process_records(raw_records)
        
        # Remove duplicates
        unique_records = processor.remove_duplicates(cleaned_records)
        
        logger.info(f"Final record count: {len(unique_records)}")
        processor_stats = processor.get_statistics()
        logger.info(f"Processor Statistics: {processor_stats}")
        
        # Export to CSV
        logger.info(f"Exporting to CSV: {output_path}")
        success = CSVExporter.export(unique_records, str(output_path))
        
        if success:
            # Validate exported CSV
            is_valid, errors = CSVExporter.validate_csv(str(output_path))
            
            if is_valid:
                file_stats = CSVExporter.get_file_stats(str(output_path))
                logger.info(f"CSV Statistics: {file_stats}")
                logger.info("Phase 1 COMPLETED SUCCESSFULLY")
                return True
            else:
                logger.error(f"CSV validation failed: {errors}")
                return False
        else:
            logger.error("Failed to export CSV")
            return False
    
    except Exception as e:
        logger.error(f"Phase 1 failed with error: {str(e)}", exc_info=True)
        return False


def scrape_phase_2(output_file: Optional[str] = None) -> bool:
    """
    Execute Phase 2 scraping (full phase - 2,700 records)
    
    Args:
        output_file: Custom output file path
        
    Returns:
        True if successful
    """
    output_path = Path(output_file) if output_file else PHASE_2_OUTPUT
    
    logger.info("="*60)
    logger.info("PHASE 2: Full Scrape (2,700 records)")
    logger.info("="*60)
    
    try:
        # Initialize scraper
        scraper = BBBScraper()
        
        # Scrape data
        logger.info("Starting Phase 2 scrape...")
        raw_records = scraper.scrape_phase_1(target_records=PHASE_2_RECORDS)  # Reuse method
        
        # Log statistics
        stats = scraper.get_statistics()
        logger.info(f"Scraper Statistics: {stats}")
        
        if not raw_records:
            logger.error("No records collected during scraping")
            return False
        
        # Process and validate data
        logger.info("Processing and validating records...")
        processor = DataProcessor()
        cleaned_records = processor.process_records(raw_records)
        
        # Remove duplicates
        unique_records = processor.remove_duplicates(cleaned_records)
        
        logger.info(f"Final record count: {len(unique_records)}")
        processor_stats = processor.get_statistics()
        logger.info(f"Processor Statistics: {processor_stats}")
        
        # Export to CSV
        logger.info(f"Exporting to CSV: {output_path}")
        success = CSVExporter.export(unique_records, str(output_path))
        
        if success:
            # Validate exported CSV
            is_valid, errors = CSVExporter.validate_csv(str(output_path))
            
            if is_valid:
                file_stats = CSVExporter.get_file_stats(str(output_path))
                logger.info(f"CSV Statistics: {file_stats}")
                logger.info("Phase 2 COMPLETED SUCCESSFULLY")
                return True
            else:
                logger.error(f"CSV validation failed: {errors}")
                return False
        else:
            logger.error("Failed to export CSV")
            return False
    
    except Exception as e:
        logger.error(f"Phase 2 failed with error: {str(e)}", exc_info=True)
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="BBB Roofing Contractor Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --phase 1                    # Run Phase 1 test scrape
  python main.py --phase 2                    # Run Phase 2 full scrape
  python main.py --phase 1 --records 100      # Custom record count
  python main.py --phase 1 --output data/custom.csv  # Custom output file
        """
    )
    
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2],
        required=True,
        help="Scraping phase (1=test, 2=full)"
    )
    
    parser.add_argument(
        "--records",
        type=int,
        help="Number of records to collect (optional)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output CSV file path (optional)"
    )
    
    args = parser.parse_args()
    
    # Run appropriate phase
    if args.phase == 1:
        success = scrape_phase_1(output_file=args.output)
    else:
        success = scrape_phase_2(output_file=args.output)
    
    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
