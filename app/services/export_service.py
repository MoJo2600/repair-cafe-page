"""
Export service for generating CSV and other export formats.
"""
import pandas as pd
from io import StringIO


class ExportService:
    """Service for handling data export operations."""
    
    @staticmethod
    def repairs_to_csv(repairs):
        """
        Convert repair records to CSV format.
        
        Args:
            repairs: List of Repair model instances
        
        Returns:
            CSV data as string
        """
        # Convert repairs to list of dicts
        repairs_data = [repair.to_dict() for repair in repairs]
        
        # Create DataFrame
        df = pd.DataFrame(repairs_data)
        
        # Convert to CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_data = csv_buffer.getvalue()
        
        return csv_data
    
    @staticmethod
    def repairs_to_dict_list(repairs):
        """
        Convert repair records to list of dictionaries.
        
        Args:
            repairs: List of Repair model instances
        
        Returns:
            List of dictionaries
        """
        return [repair.to_dict() for repair in repairs]
