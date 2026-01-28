"""
Utility functions for the BBB scraper
"""

import logging
import re
from typing import Optional, List
from config import LOG_FILE, LOG_FORMAT, LOG_LEVEL

# Configure logging
logger = logging.getLogger(__name__)


def setup_logging() -> logging.Logger:
    """Configure application logging"""
    # Create logger
    app_logger = logging.getLogger("bbb_scraper")
    app_logger.setLevel(LOG_LEVEL)
    
    # Create handlers
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(LOG_LEVEL)
    
    # Console handler with UTF-8 encoding for Windows compatibility
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    if hasattr(console_handler, 'reconfigure'):
        console_handler.reconfigure(encoding='utf-8')
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    app_logger.addHandler(file_handler)
    app_logger.addHandler(console_handler)
    
    return app_logger


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """
    Normalize phone number format
    
    Args:
        phone: Phone number string
        
    Returns:
        Normalized phone number or None
    """
    if not phone:
        return None
    
    # Remove non-numeric characters except parentheses, dash, space, and plus
    cleaned = re.sub(r"[^\d\-\(\)\s\+]", "", phone.strip())
    
    # Remove extra spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    return cleaned if cleaned else None


def normalize_email(email: Optional[str]) -> Optional[str]:
    """
    Normalize email address
    
    Args:
        email: Email address string
        
    Returns:
        Normalized email or None
    """
    if not email:
        return None
    
    email = email.strip().lower()
    
    # Basic email validation
    if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return email
    
    return None

def clean_obfuscated_email(raw_email: str) -> str:
    if not raw_email:
        return ""

    email = raw_email.strip()

    # Remove wrapping noise like !~xK_bL!
    email = re.sub(r"!~.*?!", "", email)

    # Replace common obfuscation patterns
    email = email.replace("__at__", "@")
    email = email.replace("__dot__", ".")
    email = email.replace("[at]", "@").replace("(at)", "@")
    email = email.replace("[dot]", ".").replace("(dot)", ".")

    return email.strip()

def normalize_address(address: Optional[str], city: Optional[str], 
                     state: Optional[str], postal: Optional[str]) -> str:
    """
    Create normalized full address
    
    Args:
        address: Street address
        city: City name
        state: State code
        postal: Postal code
        
    Returns:
        Formatted address string
    """
    parts = []
    
    if address:
        parts.append(address.strip())
    if city:
        parts.append(city.strip())
    if state:
        parts.append(state.strip().upper())
    if postal:
        parts.append(postal.strip())
    
    return ", ".join(parts) if parts else ""


def normalize_state(state: Optional[str]) -> Optional[str]:
    """
    Normalize state code
    
    Args:
        state: State code or name
        
    Returns:
        Two-letter state code or None
    """
    if not state:
        return None
    
    state = state.strip().upper()
    
    # Already a two-letter code
    if len(state) == 2 and state.isalpha():
        return state
    
    # Common abbreviations mapping
    state_map = {
        "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
        "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
        "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID",
        "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
        "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
        "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
        "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
        "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY",
        "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
        "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
        "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT",
        "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV",
        "WISCONSIN": "WI", "WYOMING": "WY"
    }
    
    return state_map.get(state, None)


def contains_keyword(text: Optional[str], keywords: List[str]) -> bool:
    """
    Check if text contains any of the keywords (case-insensitive)
    
    Args:
        text: Text to check
        keywords: List of keywords
        
    Returns:
        True if text contains at least one keyword
    """
    if not text:
        return False
    
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def clean_text(text: Optional[str]) -> Optional[str]:
    """
    Clean and normalize text
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text or None
    """
    if not text:
        return None
    
    # Strip whitespace
    text = text.strip()
    
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    
    return text if text else None


def extract_domain_from_url(url: Optional[str]) -> Optional[str]:
    """
    Extract domain from URL
    
    Args:
        url: Full URL
        
    Returns:
        Domain name or None
    """
    if not url:
        return None
    
    try:
        # Remove protocol
        domain = re.sub(r"^https?://", "", url.lower()).strip()
        # Remove www if present
        domain = re.sub(r"^www\.", "", domain)
        # Get domain without path
        domain = domain.split("/")[0]
        
        return domain if domain else None
    except Exception:
        return None


def sanitize_for_csv(value: Optional[str]) -> str:
    """
    Sanitize value for CSV export
    
    Args:
        value: Value to sanitize
        
    Returns:
        Sanitized string (empty string if None)
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return ""
    
    value = str(value).strip()
    
    # Remove problematic characters
    value = value.replace('"', '""')  # Escape quotes


def clean_html_tags(text: Optional[str]) -> str:
    """
    Remove HTML tags from text (e.g., <em>...</em>, <strong>...</strong>)
    
    Args:
        text: Text potentially containing HTML tags
        
    Returns:
        Cleaned text without HTML tags
    """
    if not text:
        return ""
    
    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
    
    return value
