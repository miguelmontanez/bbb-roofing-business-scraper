# All Cities Scraper - Workflow & Architecture

## Program Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│         scrape_all_cities.py - Main Entry Point                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────────┐
        │  Load display_texts.json (28K+ cities)   │
        │  Example: ["Denair, CA", "Boston, MA"]   │
        └──────────────────┬───────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────────┐
        │  Apply Filters (if --max-cities, etc)    │
        └──────────────────┬───────────────────────┘
                           │
                           ▼
    ┌─────────────────────────────────────────────────────┐
    │    FOR EACH CITY in filtered_cities:                │
    │                                                     │
    │  ┌─────────────────────────────────────────────┐    │
    │  │ 1. Parse City & State                       │    │
    │  │    "Denair, CA" → city="Denair", state="CA" │    │
    │  └─────────────────────────────────────────────┘    │
    │  ┌─────────────────────────────────────────────┐    │
    │  │ 2. Build Search URL                         │    │
    │  │    https://bbb.org/search?find_loc=Denair│  │    │
    │  │    %2CCA&find_text=Roofing+Contractors      │    │
    │  └──────────┬──────────────────────────────────┘    │
    │             │                                       │
    │             ▼                                       │
    │  ┌─────────────────────────────────────────────┐    │
    │  │ 3. Scrape Using BBBScraper                  │    │
    │  │    .scrape_city_search_url(url)             │    │
    │  │    - Follows pagination                     │    │
    │  │    - Validates records                      │    │
    │  │    - Extracts all fields                    │    │
    │  └──────────┬──────────────────────────────────┘    │
    │             │                                       │
    │             ▼                                       │
    │  ┌─────────────────────────────────────────────┐    │
    │  │ 4. Collect Results                          │    │
    │  │    records = [12 contractors from Denair]   │    │
    │  │                                             │    │
    │  │    IF records found:                        │    │
    │  │      all_records.extend(records)            │    │
    │  │    ELSE:                                    │    │
    │  │      unsupported_cities.add(city)           │    │
    │  └──────────┬──────────────────────────────────┘    │
    │             │                                       │
    │             ▼                                       │
    │  ┌─────────────────────────────────────────────┐    │
    │  │ 5. Log Progress                             │    │
    │  │    [1/28322] Processing: Denair, CA         │    │
    │  │    ✓ Scraped 12 records from Denair, CA     │    │
    │  └─────────────────────────────────────────────┘    │
    │                                                     │
    └─────────────────────┬───────────────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────────────┐
        │  All Scraping Complete                   │
        │  Collect Summary Stats:                  │
        │  - Total records: 15,342                 │
        │  - Unsupported cities: 4,521             │
        │  - Processed cities: 23,801              │
        └──────────────────┬───────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Export CSV   │ │ Save JSON    │ │ Save Summary │
    │              │ │ Unsupported  │ │              │
    │ all_cities_  │ │ Cities       │ │ scrape_      │
    │ records.csv  │ │              │ │ summary.json │
    └──────────────┘ └──────────────┘ └──────────────┘
```

## Data Flow

```
Input:
  assets/display_texts.json
  ├─ 28,322 US cities in format: "City, STATE"
  └─ Examples: "Denair, CA", "Boston, MA", "Houston, TX"

Process:
  1. Load city list from JSON
  2. For each city: build URL → scrape → validate → collect
  3. Track successful and failed cities separately

Output:
  data/all_cities_records.csv
  ├─ CSV format with standard columns
  ├─ All scraped roofing contractor records
  └─ ~500MB+ for full run (28K+ cities × avg 5-10 records/city)
  
  data/unsupported_cities.json
  ├─ JSON array of cities with no results
  └─ Examples: ["City A, ST", "City B, ST", ...]
  
  data/scrape_summary.json
  ├─ Run timestamp
  ├─ Record count
  ├─ Unsupported city count
  └─ File paths and statistics
```

## URL Building Example

```python
Input:  "Denair, CA"

Step 1: Parse
  city = "Denair"
  state = "CA"

Step 2: URL Encode
  location = "Denair, CA"
  location_encoded = "Denair%2CCA"

Step 3: Build URL
  https://www.bbb.org/search?
    find_text=Roofing+Contractors&
    find_entity=&
    find_type=&
    find_loc=Denair%2CCA&
    find_country=USA

Result: Ready to scrape!
```

## Unsupported Cities Detection

```
For each city scraping attempt:

  GET search_url
    │
    ├─ HTTP 200 & JSON parsing succeeds
    │  └─ Check: results.length > 0?
    │     ├─ YES: Add to all_records ✓
    │     └─ NO: Add to unsupported_cities ✗
    │
    ├─ HTTP Error (404, 500, etc)
    │  └─ Add to unsupported_cities ✗
    │
    ├─ Rate Limited (HTTP 429)
    │  └─ Retry with backoff
    │
    └─ Connection Error / Timeout
       └─ Add to unsupported_cities ✗
```

## Rate Limiting

```
Default: 1 request per second (respecting BBB.org limits)

Timeline for different scopes:
  
  5 cities        ~30 seconds
  50 cities       ~5 minutes
  500 cities      ~50 minutes
  1,000 cities    ~17 hours
  10,000 cities   ~170 hours (7 days)
  28,322 cities   ~480 hours (20 days) - FULL DATASET

Config in config.py:
  RATE_LIMIT = 1.0  # requests per second
  RETRY_DELAY = 2   # seconds between retries
  REQUEST_TIMEOUT = 30  # seconds per request
```

## Error Handling Strategy

```
If scraping fails for a city:

  1. Retry up to MAX_RETRIES times (default: 3)
  2. Wait RETRY_DELAY seconds between attempts
  3. If still fails: Mark as unsupported
  4. Log the error
  5. Continue to next city

This ensures:
  ✓ Temporary network issues don't stop entire run
  ✓ All failures are tracked
  ✓ No partial/corrupted data
```

## Resume/Checkpoint Strategy

```
If you need to interrupt and resume:

1. Check scrape_summary.json for last run stats
2. Count completed cities from all_cities_records.csv
3. Resume using --skip-cities parameter:

   python scrape_all_cities.py --skip-cities 5000
   
   This will skip first 5000 cities and continue from 5001

4. Subsequent runs can append to existing CSV or start fresh
```

## File Size Estimates

```
For a full run (28,322 cities, avg 5 records/city):

  all_cities_records.csv     ~300-500 MB
  unsupported_cities.json    ~100-200 KB
  scrape_summary.json        ~1 KB
  logs/scraper.log           ~100-200 MB (verbose logging)
  
  Total disk space needed    ~1 GB minimum
```

## Integration Architecture

```
scrape_all_cities.py
  │
  ├─ imports: BBBScraper (from src.scraper)
  │   └─ Uses existing scrape_city_search_url() method
  │
  ├─ imports: CSVExporter (from src.csv_exporter)
  │   └─ Uses existing export() & validate_csv() methods
  │
  ├─ imports: setup_logging (from src.utils)
  │   └─ Uses existing logging configuration
  │
  └─ imports: config settings (from config.py)
      └─ Uses existing DATA_DIR, RATE_LIMIT, etc.

✓ No modifications needed to existing codebase
✓ Fully reuses existing, tested functionality
✓ Only adds new main loop for city iteration
```
