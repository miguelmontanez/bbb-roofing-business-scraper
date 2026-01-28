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

## Output Files

| File | Description |
|------|-------------|
| `data/all_cities_records.csv` | All scraped roofing contractors |
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
- BBB rating & status
- Source URL

## Features

✓ Incremental saving (progress saved after each city)  
✓ Resume capability (--pause flag)  
✓ Record limits (stop at X total records)  
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
