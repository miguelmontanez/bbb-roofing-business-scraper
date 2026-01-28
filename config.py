"""
Configuration settings for BBB Roofing Contractor Scraper
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Logging configuration
LOG_FILE = LOGS_DIR / "scraper.log"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# BBB.org API configuration
BBB_BASE_URL = "https://www.bbb.org/api/v2/api-0.0.1"
BBB_SEARCH_ENDPOINT = "/localservice"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Scraping configuration
PHASE_1_RECORDS = 300
PHASE_2_RECORDS = 2700
TOTAL_RECORDS = PHASE_1_RECORDS + PHASE_2_RECORDS

# Records per page (based on BBB response structure)
RECORDS_PER_PAGE = 15

# Business keyword filters (business name must contain at least one)
KEYWORD_FILTERS = ["roof", "roofing", "roofer", "exteriors"]

# US states to include (lower 48 - exclude Alaska and Hawaii)
LOWER_48_STATES = {
    "AL", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI",
    "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN",
    "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
}

# Exclude Alaska and Hawaii
EXCLUDED_STATES = {"AK", "HI"}

# CSV export settings
CSV_ENCODING = "utf-8"
CSV_COLUMNS = [
    "business_name",
    "street_address",
    "city",
    "state",
    "postal_code",
    "phone",
    "email",
    "website",
    "entity_type",
    "business_started",
    "incorporated_date",
    "principal_contact",
    "business_categories",
    "source_url"
]

# Rate limiting (requests per second)
RATE_LIMIT = 1.0  # 1 request per second

# User agent for requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Proxy configuration (optional)
PROXY = None
# Example: PROXY = {"http": "http://proxy.example.com:8080", "https": "https://proxy.example.com:8080"}

# Data validation
MIN_ADDRESS_LENGTH = 3
MIN_BUSINESS_NAME_LENGTH = 2

# Output file paths
PHASE_1_OUTPUT = DATA_DIR / "phase1_records.csv"
PHASE_2_OUTPUT = DATA_DIR / "phase2_records.csv"

# Debug mode
DEBUG = False
