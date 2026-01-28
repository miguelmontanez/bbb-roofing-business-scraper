# All Cities Scraper Guide

## Overview

The `scrape_all_cities.py` script automates scraping roofing contractors from BBB.org across all US cities defined in `assets/display_texts.json`.

## Features

✅ **Loops through all US cities** - Iterates through ~28,000 cities and towns  
✅ **Builds dynamic search URLs** - Creates proper BBB search URLs for each city  
✅ **Pagination support** - Automatically handles multi-page results per city  
✅ **Unsupported cities tracking** - Saves cities with no results to JSON  
✅ **Detailed logging** - Shows progress and detailed error information  
✅ **Configurable parameters** - Control number of cities and records per city  
✅ **Summary report** - Generates summary statistics after completion  

## Usage

### Basic Usage (Scrape All Cities)

```bash
python scrape_all_cities.py
```

This will:
- Loop through all ~28,000 cities from `assets/display_texts.json`
- Scrape all available roofing contractors for each city
- Save results to `data/all_cities_records.csv`
- Track unsupported cities in `data/unsupported_cities.json`
- Generate summary in `data/scrape_summary.json`

### Limited Testing (First 10 Cities)

```bash
python scrape_all_cities.py --max-cities 10
```

### Limit Records Per City

```bash
python scrape_all_cities.py --max-cities 100 --records-per-city 50
```

This will:
- Process only the first 100 cities
- Collect max 50 records per city

### Resume from a Specific City

```bash
python scrape_all_cities.py --skip-cities 500
```

This will skip the first 500 cities and resume from city 501.

### Full Example

```bash
python scrape_all_cities.py --max-cities 1000 --records-per-city 30 --skip-cities 100
```

This will:
- Skip the first 100 cities
- Process cities 101-1100
- Collect max 30 records per city

## Output Files

### 1. `data/all_cities_records.csv`
Complete dataset with all scraped roofing contractors in CSV format.

**Columns:**
- business_name
- street_address
- city
- state
- postal_code
- phone
- email
- website
- entity_type
- business_started
- incorporated_date
- principal_contact
- business_categories
- source_url

### 2. `data/unsupported_cities.json`
List of cities where the scraper found no results or encountered errors.

Example:
```json
[
  "Adel, AL",
  "Adamsville, AL",
  "Some City, ST"
]
```

### 3. `data/scrape_summary.json`
Summary statistics from the scraping session.

Example:
```json
{
  "timestamp": "2026-01-29T14:30:45.123456",
  "total_records_collected": 15342,
  "total_unsupported_cities": 4521,
  "unsupported_cities_file": "data/unsupported_cities.json",
  "records_file": "data/all_cities_records.csv"
}
```

## URL Format

The script builds search URLs in this format:

```
https://www.bbb.org/search?find_text=Roofing+Contractors&find_entity=&find_type=&find_loc=CITY%2CSTATE&find_country=USA
```

Example for Chico, WA:
```
https://www.bbb.org/search?find_text=Roofing+Contractors&find_entity=&find_type=&find_loc=Chico%2CWA&find_country=USA
```

## How Unsupported Cities are Detected

A city is marked as "unsupported" if:
1. The BBB search returns no results
2. An error occurs while fetching/parsing the search page
3. The city format is invalid in the display_texts.json file

These cities are saved to `data/unsupported_cities.json` for reference.

## Logging

All operations are logged to both console and `logs/scraper.log`:

- ✓ indicates successful operations
- ✗ indicates failures
- Progress indicators show cities processed vs total

Example log output:
```
[1/28322] Processing: Denair, CA
✓ Scraped 12 records from Denair, CA
[2/28322] Processing: Cornwells Heights, PA
✗ No records found for Cornwells Heights, PA
```

## Rate Limiting

The scraper respects BBB.org's rate limits:
- 1 request per second by default
- Automatic backoff for 429 (rate limited) responses
- Configurable in `config.py` via `RATE_LIMIT`

## Performance Tips

### For Testing
```bash
python scrape_all_cities.py --max-cities 5
```
(5 minutes)

### For Production (First Run)
Start with a subset to test:
```bash
python scrape_all_cities.py --max-cities 1000
```
(~17 hours at 1 req/sec, collect all records)

### Resuming
If the scraper stops, resume from where it left off:
```bash
python scrape_all_cities.py --skip-cities 1000
```

## Troubleshooting

### Memory Issues with Large Datasets
If you run out of memory, process cities in batches:
```bash
python scrape_all_cities.py --max-cities 5000 --skip-cities 0
# Wait for completion, then resume
python scrape_all_cities.py --max-cities 5000 --skip-cities 5000
```

### Rate Limiting Errors
If BBB.org rate limits you frequently:
1. Increase `RETRY_DELAY` in `config.py` (default: 2 seconds)
2. Decrease `RATE_LIMIT` in `config.py` (default: 1.0 req/sec)

### Network Timeouts
Increase `REQUEST_TIMEOUT` in `config.py` (default: 30 seconds)

## Display Texts Format

The `assets/display_texts.json` file contains all US cities in format:
```json
[
  "City Name, ST",
  "Another City, TX",
  ...
]
```

Generated from `extract_city.py` which reads from `assets/us_cities.csv`.

## Related Scripts

- `main.py` - Scrape a single city by URL
- `run_city_scrape.py` - Similar functionality to main.py
- `extract_city.py` - Generate display_texts.json from CSV
