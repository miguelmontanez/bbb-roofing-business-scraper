#!/usr/bin/env python3
"""
Pre-flight checks for the all-cities scraper
Run this before starting to ensure everything is configured correctly
"""

import sys
from pathlib import Path
import json

def check_display_texts():
    """Check if display_texts.json exists and is valid"""
    print("Checking display_texts.json...")
    
    filepath = Path("assets/display_texts.json")
    
    if not filepath.exists():
        print("  ✗ File not found: assets/display_texts.json")
        print("    Run: python extract_city.py")
        return False
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"  ✗ Expected list, got {type(data).__name__}")
            return False
        
        if len(data) == 0:
            print("  ✗ File is empty")
            return False
        
        # Check format of first few entries
        for i, entry in enumerate(data[:3]):
            if not isinstance(entry, str) or "," not in entry:
                print(f"  ✗ Invalid format at entry {i}: {entry}")
                return False
        
        print(f"  ✓ Valid file with {len(data)} cities")
        print(f"    Example: {data[0]}, {data[1]}, {data[2]}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error reading file: {e}")
        return False


def check_data_directory():
    """Check if data directory exists and is writable"""
    print("\nChecking data directory...")
    
    data_dir = Path("data")
    
    if not data_dir.exists():
        try:
            data_dir.mkdir(exist_ok=True)
            print(f"  ✓ Created data directory")
        except Exception as e:
            print(f"  ✗ Cannot create data directory: {e}")
            return False
    
    try:
        test_file = data_dir / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        print(f"  ✓ Data directory is writable")
        return True
    except Exception as e:
        print(f"  ✗ Cannot write to data directory: {e}")
        return False


def check_logs_directory():
    """Check if logs directory exists and is writable"""
    print("\nChecking logs directory...")
    
    logs_dir = Path("logs")
    
    if not logs_dir.exists():
        try:
            logs_dir.mkdir(exist_ok=True)
            print(f"  ✓ Created logs directory")
        except Exception as e:
            print(f"  ✗ Cannot create logs directory: {e}")
            return False
    
    try:
        test_file = logs_dir / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        print(f"  ✓ Logs directory is writable")
        return True
    except Exception as e:
        print(f"  ✗ Cannot write to logs directory: {e}")
        return False


def check_dependencies():
    """Check if required Python packages are installed"""
    print("\nChecking Python dependencies...")
    
    required = {
        "requests": "HTTP requests",
        "pathlib": "File path utilities",
    }
    
    all_ok = True
    for package, description in required.items():
        try:
            __import__(package)
            print(f"  ✓ {package:20} ({description})")
        except ImportError:
            print(f"  ✗ {package:20} NOT INSTALLED - {description}")
            print(f"    Run: pip install {package}")
            all_ok = False
    
    return all_ok


def check_config():
    """Check if config.py is valid"""
    print("\nChecking config.py...")
    
    try:
        from config import (
            DATA_DIR, LOG_LEVEL, RATE_LIMIT, 
            MAX_RETRIES, REQUEST_TIMEOUT, RECORDS_PER_PAGE
        )
        print(f"  ✓ Config loaded successfully")
        print(f"    DATA_DIR: {DATA_DIR}")
        print(f"    RATE_LIMIT: {RATE_LIMIT} req/sec")
        print(f"    MAX_RETRIES: {MAX_RETRIES}")
        print(f"    REQUEST_TIMEOUT: {REQUEST_TIMEOUT} sec")
        return True
    except Exception as e:
        print(f"  ✗ Error loading config: {e}")
        return False


def check_scraper():
    """Check if scraper module can be imported"""
    print("\nChecking scraper module...")
    
    try:
        from src.scraper import BBBScraper
        scraper = BBBScraper()
        print(f"  ✓ BBBScraper imported successfully")
        print(f"    Base URL: {scraper.base_url}")
        return True
    except Exception as e:
        print(f"  ✗ Error importing scraper: {e}")
        return False


def check_csv_exporter():
    """Check if CSV exporter can be imported"""
    print("\nChecking CSV exporter module...")
    
    try:
        from src.csv_exporter import CSVExporter
        print(f"  ✓ CSVExporter imported successfully")
        return True
    except Exception as e:
        print(f"  ✗ Error importing CSV exporter: {e}")
        return False


def check_scrape_all_cities_script():
    """Check if scrape_all_cities.py exists"""
    print("\nChecking scrape_all_cities.py script...")
    
    script_path = Path("scrape_all_cities.py")
    
    if not script_path.exists():
        print(f"  ✗ Script not found: scrape_all_cities.py")
        return False
    
    if not script_path.is_file():
        print(f"  ✗ Not a file: scrape_all_cities.py")
        return False
    
    try:
        # Try to import it
        import scrape_all_cities
        print(f"  ✓ scrape_all_cities.py found and importable")
        return True
    except Exception as e:
        print(f"  ✗ Error with scrape_all_cities.py: {e}")
        return False


def main():
    """Run all checks"""
    print("=" * 60)
    print("BBB All Cities Scraper - Pre-flight Checks")
    print("=" * 60)
    
    checks = [
        ("Display texts", check_display_texts),
        ("Data directory", check_data_directory),
        ("Logs directory", check_logs_directory),
        ("Dependencies", check_dependencies),
        ("Config", check_config),
        ("Scraper module", check_scraper),
        ("CSV exporter", check_csv_exporter),
        ("Scraper script", check_scrape_all_cities_script),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All checks passed! Ready to run:")
        print("\n  python scrape_all_cities.py --max-cities 5")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        print("\nFor help, see:")
        print("  - QUICKSTART.md")
        print("  - SCRAPE_ALL_CITIES_GUIDE.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
