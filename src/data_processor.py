"""
Data validation and processing module
"""

import logging
import re
from typing import List, Dict, Optional
from src.utils import normalize_phone, normalize_email, normalize_state

logger = logging.getLogger("bbb_scraper")


class DataProcessor:
    """Process and validate scraped business data"""
    
    def __init__(self):
        """Initialize the data processor"""
        self.validation_errors = []
        self.cleaned_records = []
    
    def validate_email(self, email: Optional[str]) -> bool:
        """
        Validate email address format
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid email format
        """
        if not email:
            return True  # Optional field
        
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email.strip()))
    
    def validate_phone(self, phone: Optional[str]) -> bool:
        """
        Validate phone number format
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid phone format
        """
        if not phone:
            return True  # Optional field
        
        # Must contain at least 10 digits
        digits = re.sub(r"\D", "", phone)
        return len(digits) >= 10
    
    def validate_postal_code(self, postal: Optional[str], state: Optional[str]) -> bool:
        """
        Validate postal code format
        
        Args:
            postal: Postal code
            state: State code
            
        Returns:
            True if valid format
        """
        if not postal:
            return False  # Required field
        
        postal = postal.strip()
        
        # US ZIP code format: XXXXX or XXXXX-XXXX
        if re.match(r"^\d{5}(-\d{4})?$", postal):
            return True
        
        return False
    
    def validate_state(self, state: Optional[str]) -> bool:
        """
        Validate state code
        
        Args:
            state: State code
            
        Returns:
            True if valid US state
        """
        if not state:
            return False
        
        valid_states = {
            "AL", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "ID",
            "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI",
            "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
            "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN",
            "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        }
        
        return state.strip().upper() in valid_states
    
    def validate_url(self, url: Optional[str]) -> bool:
        """
        Validate URL format
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid URL
        """
        if not url:
            return True  # Optional field
        
        pattern = r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}.*$"
        return bool(re.match(pattern, url.strip()))
    
    def validate_business_name(self, name: Optional[str]) -> bool:
        """
        Validate business name
        
        Args:
            name: Business name
            
        Returns:
            True if valid
        """
        if not name:
            return False
        
        name = name.strip()
        # Minimum 2 characters, not just numbers
        return len(name) >= 2 and not name.isdigit()
    
    def clean_record(self, record: Dict) -> Dict:
        """
        Clean and normalize a business record
        
        Args:
            record: Business record dictionary
            
        Returns:
            Cleaned record
        """
        cleaned = record.copy()
        
        # Clean string fields
        for field in ["business_name", "street_address", "city", "state", 
                      "postal_code", "phone", "email", "website", "entity_type", 
                      "business_started", "incorporated_date", "principal_contact", 
                      "business_categories", "rating", "source_url"]:
            if field in cleaned and cleaned[field]:
                cleaned[field] = str(cleaned[field]).strip()
            else:
                cleaned[field] = ""
        
        # Normalize specific fields
        if cleaned.get("phone"):
            cleaned["phone"] = normalize_phone(cleaned["phone"]) or ""
        
        if cleaned.get("email"):
            cleaned["email"] = normalize_email(cleaned["email"]) or ""
        
        if cleaned.get("state"):
            normalized_state = normalize_state(cleaned["state"])
            cleaned["state"] = normalized_state if normalized_state else ""
        
        # Uppercase state
        if cleaned.get("state"):
            cleaned["state"] = cleaned["state"].upper()
        
        return cleaned
    
    def validate_record(self, record: Dict) -> tuple[bool, List[str]]:
        """
        Validate a business record against all criteria
        
        Args:
            record: Business record
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Required fields
        if not record.get("business_name"):
            errors.append("Missing business name")
        elif not self.validate_business_name(record["business_name"]):
            errors.append("Invalid business name format")
        
        if not record.get("street_address"):
            errors.append("Missing street address")
        
        if not record.get("city"):
            errors.append("Missing city")
        
        if not record.get("state"):
            errors.append("Missing state")
        elif not self.validate_state(record["state"]):
            errors.append("Invalid state code")
        
        if not record.get("postal_code"):
            errors.append("Missing postal code")
        elif not self.validate_postal_code(record["postal_code"], record.get("state")):
            errors.append("Invalid postal code format")
        
        # Optional fields validation
        if record.get("email") and not self.validate_email(record["email"]):
            errors.append("Invalid email format")
        
        if record.get("phone") and not self.validate_phone(record["phone"]):
            errors.append("Invalid phone format")
        
        if record.get("website") and not self.validate_url(record["website"]):
            errors.append("Invalid website URL format")
        
        return (len(errors) == 0, errors)
    
    def process_records(self, records: List[Dict]) -> List[Dict]:
        """
        Process and clean multiple records
        
        Args:
            records: List of business records
            
        Returns:
            List of validated and cleaned records
        """
        logger.info(f"Processing {len(records)} records...")
        
        valid_records = []
        invalid_count = 0
        
        for i, record in enumerate(records, 1):
            # Clean the record first
            cleaned = self.clean_record(record)
            
            # Validate the cleaned record
            is_valid, errors = self.validate_record(cleaned)
            
            if is_valid:
                valid_records.append(cleaned)
                logger.debug(f"Record {i} valid: {cleaned.get('business_name')}")
            else:
                invalid_count += 1
                logger.warning(f"Record {i} invalid ({cleaned.get('business_name')}): {', '.join(errors)}")
                self.validation_errors.append({
                    "record": cleaned,
                    "errors": errors
                })
        
        self.cleaned_records = valid_records
        logger.info(f"Processing complete: {len(valid_records)} valid, {invalid_count} invalid")
        
        return valid_records
    
    def remove_duplicates(self, records: List[Dict]) -> List[Dict]:
        """
        Remove duplicate records based on business name and address
        
        Args:
            records: List of records
            
        Returns:
            List with duplicates removed
        """
        logger.info(f"Removing duplicates from {len(records)} records...")
        
        seen = set()
        unique_records = []
        
        for record in records:
            # Create a key from name and address
            key = (
                record.get("business_name", "").lower().strip(),
                record.get("street_address", "").lower().strip(),
                record.get("city", "").lower().strip(),
                record.get("state", "").upper()
            )
            
            if key not in seen:
                seen.add(key)
                unique_records.append(record)
            else:
                logger.debug(f"Duplicate removed: {record.get('business_name')}")
        
        logger.info(f"Removed {len(records) - len(unique_records)} duplicates, {len(unique_records)} unique records remaining")
        
        return unique_records
    
