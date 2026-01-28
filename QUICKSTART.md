# Quick Start Guide - All Cities Scraper

## Installation Check

```bash
# Make sure you have the project dependencies installed
pip install -r requirements.txt
```

## First Run - Test with 5 Cities (3-5 minutes)

```bash
python scrape_all_cities.py --max-cities 5
```

**What to expect:**
- Real-time progress logging
- Each city shows: `[X/5] Processing: City, ST`
- Results: 5-50 records total
- Output: `data/all_cities_records.csv`

## Monitor the Output

```bash
# Watch the CSV grow in real-time
Get-Content data/all_cities_records.csv | Measure-Object -Line  # PowerShell

# Or check the log
tail -f logs/scraper.log
```

## Review Results

```bash
# Check how many records were collected
python -c "
import csv
with open('data/all_cities_records.csv') as f:
    count = sum(1 for _ in csv.DictReader(f))
    print(f'Total records: {count}')
"

# Check unsupported cities
python -c "
import json
with open('data/unsupported_cities.json') as f:
    cities = json.load(f)
    print(f'Unsupported cities: {len(cities)}')
"

# View summary
python -c "
import json
with open('data/scrape_summary.json') as f:
    summary = json.load(f)
    print(json.dumps(summary, indent=2))
"
```

## Next Steps

### Option A: Small Test (50 cities, ~5 minutes)
```bash
python scrape_all_cities.py --max-cities 50 --records-per-city 30
```

### Option B: Medium Run (1000 cities, ~17 hours)
```bash
python scrape_all_cities.py --max-cities 1000
```

### Option C: Full Production (28,322 cities, ~20 days)
```bash
# WARNING: This takes a long time and uses a lot of disk space!
python scrape_all_cities.py
```

## If You Need to Stop and Resume

```bash
# Check which cities have been processed
tail -20 data/all_cities_records.csv | head -1  # Get last city processed

# Resume from city 1000 (skipping first 999)
python scrape_all_cities.py --skip-cities 1000
```

## Understanding the Output

### CSV File (`data/all_cities_records.csv`)
Contains all roofing contractors with:
- Business name
- Address, City, State, ZIP
- Phone, Email, Website
- Entity type, dates, principal contact
- Categories, rating, BBB status
- Source URL

### JSON Files
```
data/unsupported_cities.json  - Cities with no results
data/scrape_summary.json      - Run statistics
```

### Logs
```
logs/scraper.log - Detailed execution log
```

## Common Commands

```bash
# Test with 10 cities, 20 records max each
python scrape_all_cities.py --max-cities 10 --records-per-city 20

# Process 5000 cities (skip first 2000 to resume)
python scrape_all_cities.py --max-cities 5000 --skip-cities 2000

# Process everything
python scrape_all_cities.py

# See all options
python scrape_all_cities.py --help
```

## Troubleshooting

### Getting Rate Limited?
```bash
# Add longer delay between requests
# Edit config.py and change:
RETRY_DELAY = 5  # was 2
RATE_LIMIT = 0.5  # was 1.0
```

### Running Out of Memory?
```bash
# Process in smaller batches
python scrape_all_cities.py --max-cities 5000 --skip-cities 0
# Wait for completion
python scrape_all_cities.py --max-cities 5000 --skip-cities 5000
```

### Seeing Connection Errors?
```bash
# Increase timeout
# Edit config.py and change:
REQUEST_TIMEOUT = 60  # was 30
```

## Performance Benchmarks

```
Test Run (5 cities):
  Time: ~3-5 minutes
  Records: 10-50
  Memory: ~50 MB
  
Small Run (50 cities):
  Time: ~50 minutes
  Records: 100-500
  Memory: ~100 MB
  
Medium Run (1000 cities):
  Time: ~17 hours
  Records: 5,000-15,000
  Memory: ~500 MB
  
Large Run (10,000 cities):
  Time: ~7 days
  Records: 50,000-150,000
  Memory: ~2 GB
```

## Next Steps After Scraping

1. **Analyze the CSV**
   - Load into Excel, Python, or database
   - Filter by state, rating, or other criteria
   - Find companies with email/phone

2. **Export Specific States**
   ```bash
   python -c "
   import pandas as pd
   df = pd.read_csv('data/all_cities_records.csv')
   ca_only = df[df['state'] == 'CA']
   ca_only.to_csv('data/california_contractors.csv', index=False)
   "
   ```

3. **Database Import**
   - Import CSV into PostgreSQL, MySQL, or SQLite
   - Create indexes for faster queries
   - Set up regular re-scraping jobs

4. **Data Quality Checks**
   - Verify email addresses
   - Validate phone numbers
   - Check for duplicates

## Questions?

See:
- `SCRAPE_ALL_CITIES_GUIDE.md` - Full documentation
- `ARCHITECTURE_DIAGRAM.md` - How it works
- `examples_scrape_all_cities.py` - More examples
