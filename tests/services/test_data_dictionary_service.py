import unittest
import sys
import os
from unittest.mock import MagicMock, patch

from services.data_dictionary_service import DataDictionaryService
from errors import SchemaDescriptorError


class TestDataDictionaryService(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.bq_service = MagicMock()
        self.llm_service = MagicMock()
        self.data_dict_service = DataDictionaryService(
            bq_service=self.bq_service,
            llm_service=self.llm_service
        )
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.data_dict_service.bq_service, self.bq_service)
        self.assertEqual(self.data_dict_service.llm_service, self.llm_service)
    
    def test_build_data_dictionary(self):
        """Test build_data_dictionary method."""
        # Mock BigQuery service methods
        self.bq_service.list_tables.return_value = ["table1", "table2"]
        
        # Mock table
        mock_table1 = MagicMock()
        mock_table1.schema = [MagicMock(name="col1", field_type="STRING")]
        
        mock_table2 = MagicMock()
        mock_table2.schema = [MagicMock(name="col2", field_type="INTEGER")]
        
        self.bq_service.get_table.side_effect = [mock_table1, mock_table2]
        
        # Mock sample data
        self.bq_service.get_table_sample.return_value = [{"col1": "sample1"}]
        
        # Mock column sample
        self.bq_service.get_column_sample.return_value = ["sample1"]
        
        # Mock LLM service
        self.llm_service.get_dataset_description.return_value = "Dataset description"
        self.llm_service.get_table_description.return_value = "Table description"
        self.llm_service.get_column_description.return_value = "Column description"
        
        # Create a mock progress callback
        mock_callback = MagicMock()
        
        result = self.data_dict_service.build_data_dictionary(
            project_id="project",
            dataset_id="dataset",
            instructions="Test instructions",
            limit_per_table=5,
            progress_callback=mock_callback
        )
        
        # Verify the BigQuery service calls
        self.bq_service.list_tables.assert_called_once()
        self.assertEqual(self.bq_service.get_table.call_count, 2)
        self.assertEqual(self.bq_service.get_table_sample.call_count, 2)
        
        # Verify the LLM service calls
        self.llm_service.get_dataset_description.assert_called_once()
        self.assertEqual(self.llm_service.get_table_description.call_count, 2)
        self.assertEqual(self.llm_service.get_column_description.call_count, 2)
        
        # Verify progress callback was called
        self.assertGreater(mock_callback.call_count, 0)
        
        # Verify the structure of the returned data dictionary
        self.assertIn("dataset", result)
        self.assertIn("description", result["dataset"])
        self.assertIn("tables", result["dataset"])
        self.assertEqual(len(result["dataset"]["tables"]), 2)
        
    def test_build_data_dictionary_error(self):
        """Test build_data_dictionary with error."""
        # Mock BigQuery service to raise an error
        self.bq_service.list_tables.side_effect = Exception("API Error")
        
        with self.assertRaises(SchemaDescriptorError):
            self.data_dict_service.build_data_dictionary(
                project_id="project",
                dataset_id="dataset"
            )
            
    def test_describe_column(self):
        """Test describe_column method."""
        # Mock column sample
        self.bq_service.get_column_sample.return_value = ["sample1", "sample2"]
        
        # Mock LLM service
        self.llm_service.get_column_description.return_value = "Column description"
        
        result = self.data_dict_service.describe_column(
            table_id="dataset.table",
            column_name="column",
            sample_limit=10,
            instructions="Test instructions"
        )
        
        # Verify the result
        self.assertEqual(result, "Column description")
        
        # Verify method calls
        self.bq_service.get_column_sample.assert_called_once()
        self.llm_service.get_column_description.assert_called_once()
        
    def test_describe_table(self):
        """Test describe_table method."""
        # Mock table sample
        mock_sample = [
            {"col1": "value1", "col2": 123},
            {"col1": "value2", "col2": 456}
        ]
        self.bq_service.get_table_sample.return_value = mock_sample
        
        # Mock LLM service
        self.llm_service.get_table_description.return_value = "Table description"
        
        result = self.data_dict_service.describe_table(
            table_id="dataset.table",
            sample_limit=10,
            instructions="Test instructions"
        )
        
        # Verify the result
        self.assertEqual(result, "Table description")
        
        # Verify method calls
        self.bq_service.get_table_sample.assert_called_once()
        self.llm_service.get_table_description.assert_called_once()


if __name__ == '__main__':
    unittest.main()