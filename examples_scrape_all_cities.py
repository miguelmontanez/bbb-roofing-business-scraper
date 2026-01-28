#!/usr/bin/env python3
"""
Quick examples for running the all-cities scraper

Run one of these commands to get started:
"""

# Example 1: Test with just 5 cities (quick test)
# python scrape_all_cities.py --max-cities 5

# Example 2: Test with 50 cities, max 20 records each (still quick)
# python scrape_all_cities.py --max-cities 50 --records-per-city 20

# Example 3: Full scrape - all cities, all records (takes many hours)
# python scrape_all_cities.py

# Example 4: Resume from city 1000 (if previous run stopped)
# python scrape_all_cities.py --skip-cities 1000

# Example 5: Process 10000 cities with 100 records max per city
# python scrape_all_cities.py --max-cities 10000 --records-per-city 100

if __name__ == "__main__":
    print(__doc__)
