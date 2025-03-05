import unittest
import sys
import os
from unittest.mock import MagicMock, patch
import datetime

from utils.bq_utils import handle_partition_filter, flatten_column_dict


class TestBigQueryUtils(unittest.TestCase):
    
    def test_handle_partition_filter_no_partitioning(self):
        """Test handle_partition_filter with no partitioning."""
        table = MagicMock()
        table.time_partitioning = None
        result = handle_partition_filter(table)
        self.assertEqual(result, "")
    
    def test_handle_partition_filter_with_partitioning_no_dates(self):
        """Test handle_partition_filter with partitioning but no date parameters."""
        table = MagicMock()
        table.time_partitioning = MagicMock()
        table.time_partitioning.field = "event_date"
        
        # Need to mock the return value of today().isoformat()
        mock_date = MagicMock()
        mock_date.today.return_value.isoformat.return_value = "2023-01-15"
        
        with patch("datetime.date", mock_date):
            result = handle_partition_filter(table)
            self.assertEqual(result, "WHERE `event_date` = '2023-01-15'")
    
    def test_handle_partition_filter_with_partitioning_and_dates(self):
        """Test handle_partition_filter with partitioning and date parameters."""
        table = MagicMock()
        table.time_partitioning = MagicMock()
        table.time_partitioning.field = "event_date"
        
        # Test with start and end dates
        result = handle_partition_filter(table, start_date="2023-01-01", end_date="2023-01-31")
        self.assertEqual(result, "WHERE `event_date` BETWEEN '2023-01-01' AND '2023-01-31'")
        
        # Test with only start date
        result = handle_partition_filter(table, start_date="2023-01-01")
        self.assertEqual(result, "WHERE `event_date` >= '2023-01-01'")
        
        # Test with only end date
        result = handle_partition_filter(table, end_date="2023-01-31")
        self.assertEqual(result, "WHERE `event_date` <= '2023-01-31'")
    
    def test_handle_partition_filter_with_default_partitioning(self):
        """Test handle_partition_filter with default ingestion-time partitioning."""
        table = MagicMock()
        table.time_partitioning = MagicMock()
        table.time_partitioning.field = None
        
        result = handle_partition_filter(table, start_date="2023-01-01", end_date="2023-01-31")
        self.assertEqual(result, "WHERE `_PARTITIONDATE` BETWEEN '2023-01-01' AND '2023-01-31'")
    
    def test_flatten_column_dict_empty(self):
        """Test flatten_column_dict with empty dictionary."""
        result = flatten_column_dict({})
        self.assertEqual(result, {})
    
    def test_flatten_column_dict_simple(self):
        """Test flatten_column_dict with simple dictionary."""
        columns = {
            "col1": {"llm_description": "Description 1"},
            "col2": {"llm_description": "Description 2"}
        }
        result = flatten_column_dict(columns)
        expected = {
            "col1": {"llm_description": "Description 1"},
            "col2": {"llm_description": "Description 2"}
        }
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()