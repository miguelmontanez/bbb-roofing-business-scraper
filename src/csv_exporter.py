"""
CSV export functionality
"""

import logging
import csv
from pathlib import Path
from typing import List, Dict, Optional
from config import CSV_COLUMNS, CSV_ENCODING

logger = logging.getLogger("bbb_scraper")


class CSVExporter:
    """Export business data to CSV format"""
    
    @staticmethod
    def export(records: List[Dict], output_path: str, include_header: bool = True) -> bool:
        """
        Export records to CSV file
        
        Args:
            records: List of business records
            output_path: Path to output CSV file
            include_header: Whether to include header row
            
        Returns:
            True if successful, False otherwise
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Exporting {len(records)} records to {output_path}")
            
            with open(output_path, "w", newline="", encoding=CSV_ENCODING) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS, restval="")
                
                if include_header:
                    writer.writeheader()
                
                for i, record in enumerate(records, 1):
                    # Ensure all required columns are present
                    row = {col: record.get(col, "") for col in CSV_COLUMNS}
                    writer.writerow(row)
                    
                    if i % 100 == 0:
                        logger.debug(f"Exported {i}/{len(records)} records...")
            
            logger.info(f"Successfully exported {len(records)} records to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {str(e)}")
            return False
    
    @staticmethod
    def export_with_metadata(records: List[Dict], output_path: str, 
                            metadata: Optional[Dict] = None) -> bool:
        """
        Export records with metadata (timestamp, record count, etc.)
        
        Args:
            records: List of business records
            output_path: Path to output CSV file
            metadata: Optional metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        return CSVExporter.export(records, output_path, include_header=True)
    
    @staticmethod
    def validate_csv(file_path: str) -> tuple[bool, List[str]]:
        """
        Validate CSV file structure and content
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
                return (False, errors)
            
            with open(file_path, "r", encoding=CSV_ENCODING) as csvfile:
                reader = csv.DictReader(csvfile)
                
                if reader.fieldnames is None:
                    errors.append("CSV file is empty")
                    return (False, errors)
                
                # Check headers
                missing_columns = set(CSV_COLUMNS) - set(reader.fieldnames)
                if missing_columns:
                    errors.append(f"Missing columns: {missing_columns}")
                
                # Check records
                record_count = 0
                for row_num, row in enumerate(reader, 2):  # Start from 2 (after header)
                    record_count += 1
                    
                    # Check required fields
                    if not row.get("business_name", "").strip():
                        errors.append(f"Row {row_num}: Missing business name")
                    
                    if not row.get("source_url", "").strip():
                        errors.append(f"Row {row_num}: Missing source URL")
                
                if record_count == 0:
                    errors.append("CSV contains no data rows")
            
            return (len(errors) == 0, errors)
            
        except Exception as e:
            errors.append(f"Error reading CSV: {str(e)}")
            return (False, errors)
    
    @staticmethod
    def get_file_stats(file_path: str) -> Dict:
        """
        Get statistics about a CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Statistics dictionary
        """
        stats = {
            "file_path": str(file_path),
            "record_count": 0,
            "file_size_bytes": 0,
            "has_header": False,
            "columns": []
        }
        
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return stats
            
            stats["file_size_bytes"] = file_path.stat().st_size
            
            with open(file_path, "r", encoding=CSV_ENCODING) as csvfile:
                reader = csv.DictReader(csvfile)
                
                if reader.fieldnames:
                    stats["has_header"] = True
                    stats["columns"] = list(reader.fieldnames)
                
                for _ in reader:
                    stats["record_count"] += 1
            
        except Exception as e:
            logger.warning(f"Error getting file stats: {str(e)}")
        
        return stats
