import sys
import json
from pathlib import Path
from src.scraper import BBBScraper

DEFAULT_URL = (
    "https://www.bbb.org/search?find_country=USA&find_entity=10126-000&"
    "find_latlng=41.870171%2C-87.671737&find_loc=Chicago%2C%20IL&"
    "find_text=Roofing%20Contractors&find_type=Category"
)

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    target = int(sys.argv[2]) if len(sys.argv) > 2 else None

    scraper = BBBScraper()
    records = scraper.scrape_city_search_url(url, target_records=target)

    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "chicago_records.json"

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"Wrote {len(records)} records to {out_path}")

if __name__ == "__main__":
    main()
