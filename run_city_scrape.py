import sys
from pathlib import Path
from src.scraper import BBBScraper
from src.csv_exporter import CSVExporter
from config import DATA_DIR
from src.utils import setup_logging

# Ensure logging handlers are configured for console + file
logger = setup_logging()

DEFAULT_URL = (
    "https://www.bbb.org/search?find_country=USA&find_entity=10126-000&"
    "find_latlng=41.870171%2C-87.671737&find_loc=Chicago%2C%20IL&"
    "find_text=Roofing%20Contractors&find_type=Category"
)


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    target = int(sys.argv[2]) if len(sys.argv) > 2 else None

    logger.info(f"Starting city scrape for URL: {url} target={target}")

    scraper = BBBScraper()
    records = scraper.scrape_city_search_url(url, target_records=target)

    out_dir = DATA_DIR
    out_dir.mkdir(exist_ok=True)
    out_csv = out_dir / "chicago_records.csv"

    success = CSVExporter.export(records, str(out_csv))
    logger.info(f"Exported {len(records)} records to {out_csv} -> {success}")

    is_valid, errors = CSVExporter.validate_csv(str(out_csv))
    if not is_valid:
        logger.error("CSV validation failed with errors:")
        for e in errors:
            logger.error(" - %s", e)
    else:
        logger.info("CSV validation passed.")


if __name__ == "__main__":
    main()
