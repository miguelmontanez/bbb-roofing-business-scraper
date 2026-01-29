# BBB Roofing Contractor Scraper

A Python-based web scraper to collect roofing contractor business records from BBB.org across all US cities.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Extract City List (First Time Only)
```bash
python extract_city.py
```

### 3. Run Scraper

**Test run (5 cities, 200 records limit):**
```bash
python scrape_all_cities.py --records 200 --reset
```

**Resume from progress:**
```bash
python scrape_all_cities.py --pause
```

**Full scrape (all cities):**
```bash
python scrape_all_cities.py
```

**With custom options:**
```bash
python scrape_all_cities.py --max-cities 1000 --records 5000 --records-per-city 50
```

## Command Options

### scrape_all_cities.py

| Option | Description |
|--------|-------------|
| `--reset` | Clear progress and start from first city |
| `--pause` | Resume from last processed city |
| `--records N` | Total record limit (stops when reached) |
| `--records-per-city N` | Max records per city |
| `--max-cities N` | Process only N cities |
| `--skip-cities N` | Skip first N cities |
| `--start-index N` | Start at city index N (1-based) |
| `--end-index N` | End at city index N (1-based, inclusive) |

**Examples:**

Multi-device scraping (split by index range):
```bash
# Device 1: Cities 1-5000
python scrape_all_cities.py --start-index 1 --end-index 5000

# Device 2: Cities 5001-10000
python scrape_all_cities.py --start-index 5001 --end-index 10000

# Device 3: Cities 10001 onwards
python scrape_all_cities.py --start-index 10001
```

Output filenames will reflect the parameters:
```
all_cities_records_i1-5000.csv          # start-index and end-index
all_cities_records_i5001-10000.csv      # another range
all_cities_records_i10001-.csv          # open-ended range
all_cities_records_r200.csv             # records limit only
all_cities_records_i1-100_r200.csv      # combined options
all_cities_records_resume.csv           # resume mode
```

**CSV Backup:**
All existing CSV files are automatically backed up before each run with the current date:
```
all_cities_records.csv  -> all_cities_records_2026-01-29.csv
all_cities_records_i1-5000.csv -> all_cities_records_i1-5000_2026-01-29.csv
```

### extract_city.py

Generates the list of all US cities from `assets/us_cities.csv`:
```bash
python extract_city.py
```
Output: `assets/display_texts.json` (28,322 cities)

### run_city_scrape.py

Scrape a single city by search URL:
```bash
python run_city_scrape.py
```

### merge_csvs.py

Merge partial CSV files from multi-device/batch runs:
```bash
python merge_csvs.py --input data/*.csv --output data/merged_records.csv
```

With deduplication (by business_name + address + city + state):
```bash
python merge_csvs.py --input data/all_cities_records*.csv --output data/final.csv --dedupe
```

## Output Files

| File | Description |
|------|-------------|
| `data/all_cities_records*.csv` | Scraped roofing contractors (filename varies by command options) |
| `data/all_cities_records*_YYYY-MM-DD.csv` | Automatic backups of previous runs |
| `data/scrape_progress.json` | Progress tracking (for resume) |
| `data/scrape_summary.json` | Session statistics |
| `logs/scraper.log` | Detailed execution log |

## Data Collected

For each roofing contractor:
- Business name (HTML tags removed)
- Address (street, city, state, ZIP)
- Phone & Email
- Website
- Principal contact
- Entity type
- Business dates
- Categories
- Source URL

## Features

✓ Incremental saving (progress saved after each city)  
✓ Resume capability (--pause flag)  
✓ Record limits (stop at X total records)  
✓ Multi-device scraping (--start-index and --end-index for splitting)  
✓ Duplicate business name skipping (per city)  
✓ Automatic CSV backup before each run  
✓ CSV merge utility (combine partial runs with optional dedup)  
✓ HTML tag cleanup (removes <em>, <strong>, etc)  
✓ Clear logging (structured, easy to follow)  
✓ Unicode compatible (no encoding errors on Windows)  
✓ Rate limiting (1 req/sec, respects BBB.org)  

## Configuration

Edit `config.py` to adjust:
- `RATE_LIMIT` - Requests per second
- `MAX_RETRIES` - Retry failed requests
- `REQUEST_TIMEOUT` - Request timeout seconds
- `RETRY_DELAY` - Delay between retries

## Project Structure

```
.
├── scrape_all_cities.py      # Main scraper (all cities)
├── run_city_scrape.py        # Single city scraper
├── extract_city.py           # Generate city list
├── extract_city_from_bbb.py  # Extract from BBB
│
├── src/
│   ├── scraper.py            # Scraper class
│   ├── csv_exporter.py       # CSV export
│   └── utils.py              # Utilities (including HTML cleanup)
│
├── data/                      # Output directory
├── logs/                      # Log files
├── config.py                  # Configuration
├── README.md                  # This file
└── requirements.txt           # Dependencies
```

## Dependencies

- `requests` - HTTP requests
- Standard library: `json`, `csv`, `logging`, `re`

## Logging

All operations logged to:
- Console (stdout)
- File: `logs/scraper.log`

Log format: `[TIMESTAMP] [LEVEL] [MESSAGE]`

Common log prefixes:
- `[SUCCESS]` - Operation completed
- `[ERROR]` - Error occurred
- `[WARNING]` - Warning message
- `[INFO]` - Information
- `[CONFIG]` - Configuration
- `[ACTION]` - Action being taken
- `[NO-RESULTS]` - City has no contractors
- `[LIMIT-REACHED]` - Record limit hit
