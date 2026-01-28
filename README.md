# BBB Roofing Contractor Scraper

A Python-based web scraper to collect roofing contractor business records from BBB.org across the lower 48 United States.

## Project Overview

This project scrapes business data from BBB.org in two phases:

## Business Inclusion Criteria

Each business must meet ALL of the following:
- Located in the lower 48 U.S. states
- Has a physical or mailing address
- Business name includes at least one of: `roof`, `roofing`, `roofer`, `exteriors`

## Required Data Fields

- Business name
- Mailing address (street, city, state, ZIP)
- Principal contact(s) / owner / key contact
- Business incorporated date
- Business started / year established
- Entity type (LLC, Inc., Corporation, etc.)
- Website URL
- Phone number
- Email address
- Business categories
- Source URL (for verification)

## Project Structure

```
bbb-roof-company-scraper/
├── src/
│   ├── scraper.py           # Main scraper class
│   ├── data_processor.py    # Data validation and cleaning
│   ├── csv_exporter.py      # CSV export functionality
│   └── utils.py             # Utility functions
├── data/
│   └── phase1_records.csv   # Phase 1 output (300 records)
├── logs/
│   └── scraper.log          # Application logs
├── config.py                # Configuration settings
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure settings** in `config.py` (optional)

3. **Run the scraper:**
   ```bash
   python main.py
   ```

## Usage

```bash
python main.py
```

### Custom Configuration

```bash
python main.py --records 300 --output data/custom_output.csv
```

## Output Format

- **Format**: CSV (Excel-compatible)
- **Encoding**: UTF-8
- **One row per business**
- **No duplicate records**
- **Missing data left blank** (no "N/A" placeholders)

## Quality Assurance

Validation checks:
- ✓ Accurate keyword filtering
- ✓ Consistent formatting
- ✓ Valid addresses
- ✓ Reasonable field completeness

## Logging

Application logs are written to `logs/scraper.log` with:
- Timestamp
- Log level (INFO, WARNING, ERROR)
- Message content

## Error Handling

- Network errors are logged and retried
- Invalid data is flagged and excluded
- Rate limiting respected
- Graceful degradation for missing fields

## Requirements

- Python 3.8+
- requests
- beautifulsoup4
- pandas
- python-dotenv
- lxml

## Notes

- BBB.org API endpoints are reverse-engineered from browser requests
- Rate limiting is implemented to respect server resources
- All data collection complies with BBB.org's terms of service
- Source URLs are preserved for verification purposes

## Status

- [x] Project structure created
- [ ] scraper implementation
- [ ] validation and testing
