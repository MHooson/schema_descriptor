import unittest
import sys
import os
from unittest.mock import MagicMock, patch
import datetime
import json

from services.llm_service import LLMService
from errors import LLMError


class TestLLMService(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.llm_service = LLMService(api_key="test_key", model="test-model", max_tokens=100, temperature=0.5)
        self.llm_service._test_mode = True
    
    @patch('openai.ChatCompletion.create')
    def test_generate_text_success(self, mock_create):
        """Test generate_text with successful API call."""
        # Mock the OpenAI API response
        mock_create.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response"
                    }
                }
            ]
        }
        
        result = self.llm_service.generate_text("Test prompt")
        self.assertEqual(result, "This is a test response")
        mock_create.assert_called_once()
    
    @patch('openai.ChatCompletion.create')
    def test_generate_text_cached(self, mock_create):
        """Test generate_text with cached response."""
        # Add an item to the cache
        self.llm_service.cache["Test prompt"] = "Cached response"
        
        result = self.llm_service.generate_text("Test prompt")
        self.assertEqual(result, "Cached response")
        mock_create.assert_not_called()
    
    @patch('openai.ChatCompletion.create')
    @patch('time.sleep')
    def test_generate_text_retry_success(self, mock_sleep, mock_create):
        """Test generate_text with retry and eventual success."""
        # Mock the OpenAI API to fail once then succeed
        mock_create.side_effect = [
            Exception("503 Service Unavailable"),
            {
                "choices": [
                    {
                        "message": {
                            "content": "Retry response"
                        }
                    }
                ]
            }
        ]
        
        result = self.llm_service.generate_text("Test prompt")
        self.assertEqual(result, "Retry response")
        self.assertEqual(mock_create.call_count, 2)
        mock_sleep.assert_called_once()
    
    @patch('openai.ChatCompletion.create')
    @patch('time.sleep')
    def test_generate_text_all_retries_fail(self, mock_sleep, mock_create):
        """Test generate_text with all retries failing."""
        # Mock the OpenAI API to always fail
        mock_create.side_effect = Exception("503 Service Unavailable")
        
        with self.assertRaises(LLMError):
            self.llm_service.generate_text("Test prompt", max_retries=3)
        
        self.assertEqual(mock_create.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # Called once for each retry except the last
    
    def test_generate_text_no_api_key(self):
        """Test generate_text with no API key."""
        service = LLMService(api_key=None)
        
        with self.assertRaises(LLMError):
            service.generate_text("Test prompt")
    
    @patch.object(LLMService, 'generate_text')
    def test_generate_text_safely_success(self, mock_generate_text):
        """Test generate_text_safely with successful API call."""
        mock_generate_text.return_value = "Good response"
        
        result = self.llm_service.generate_text_safely("Test prompt", "Default text")
        self.assertEqual(result, "Good response")
    
    @patch('openai.ChatCompletion.create')
    def test_generate_text_safely_fallback(self, mock_create):
        """Test generate_text_safely with API failure and fallback to default."""
        mock_create.side_effect = Exception("API Error")
        
        result = self.llm_service.generate_text_safely("Test prompt", "Default text")
        self.assertEqual(result, "Default text")
    
    @patch('openai.ChatCompletion.create')
    def test_generate_text_safely_multiple_models(self, mock_create):
        """Test generate_text_safely trying multiple models."""
        self.llm_service.model = "gpt-3.5-turbo"
        
        # First model fails, second model succeeds
        mock_create.side_effect = [
            Exception("API Error"),
            {
                "choices": [
                    {
                        "message": {
                            "content": "Response from fallback model"
                        }
                    }
                ]
            }
        ]
        
        result = self.llm_service.generate_text_safely("Test prompt", "Default text")
        self.assertEqual(result, "Response from fallback model")
        self.assertEqual(mock_create.call_count, 2)
    
    def test_mask_sample_value(self):
        """Test mask_sample_value with different types."""
        # Test with None
        self.assertEqual(self.llm_service.mask_sample_value(None), "NULL")
        
        # Test with datetime
        dt = datetime.datetime(2023, 1, 15, 12, 30, 45)
        self.assertEqual(self.llm_service.mask_sample_value(dt), "2023-01-15T12:30:45")
        
        # Test with numbers
        self.assertEqual(self.llm_service.mask_sample_value(123), 123)
        self.assertEqual(self.llm_service.mask_sample_value(123.45), 123.45)
        
        # Test with short string
        self.assertEqual(self.llm_service.mask_sample_value("abc"), "abc")
        
        # Test with long string
        self.assertEqual(self.llm_service.mask_sample_value("abcdefghijklmnopqrstuvwxyz"), "abcdefghij...")
        
        # Test with complex object
        obj = {"name": "test", "value": 123, "nested": {"a": 1, "b": 2}}
        expected = json.dumps(obj)[:50]
        self.assertTrue(self.llm_service.mask_sample_value(obj).startswith(expected))
    
    @patch.object(LLMService, 'generate_text_safely')
    def test_get_column_description(self, mock_generate):
        """Test get_column_description method."""
        mock_generate.return_value = "Generated column description"
        
        result = self.llm_service.get_column_description(
            "project.dataset.table", 
            "column_name", 
            [1, 2, 3, 4, 5]
        )
        
        self.assertEqual(result, "Generated column description")
        mock_generate.assert_called_once()
        # Check that the prompt contains the table and column name
        call_args = mock_generate.call_args[0]
        self.assertIn("project.dataset.table", call_args[0])
        self.assertIn("column_name", call_args[0])
        self.assertIn("1, 2, 3, 4, 5", call_args[0])
    
    @patch.object(LLMService, 'generate_text_safely')
    def test_get_table_description(self, mock_generate):
        """Test get_table_description method."""
        mock_generate.return_value = "Generated table description"
        
        columns_and_samples = {
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        }
        
        result = self.llm_service.get_table_description(
            "project.dataset.table",
            columns_and_samples
        )
        
        self.assertEqual(result, "Generated table description")
        mock_generate.assert_called_once()
        # Check that the prompt contains the table name and columns
        call_args = mock_generate.call_args[0]
        self.assertIn("project.dataset.table", call_args[0])
        self.assertIn("col1", call_args[0])
        self.assertIn("col2", call_args[0])
    
    @patch.object(LLMService, 'generate_text_safely')
    def test_get_dataset_description(self, mock_generate):
        """Test get_dataset_description method."""
        mock_generate.return_value = "Generated dataset description"
        
        table_ids = ["table1", "table2", "table3"]
        
        result = self.llm_service.get_dataset_description(
            "project.dataset",
            table_ids
        )
        
        self.assertEqual(result, "Generated dataset description")
        mock_generate.assert_called_once()
        # Check that the prompt contains the dataset name and tables
        call_args = mock_generate.call_args[0]
        self.assertIn("project.dataset", call_args[0])
        self.assertIn("table1", call_args[0])
        self.assertIn("table2", call_args[0])
        self.assertIn("table3", call_args[0])


if __name__ == '__main__':
    unittest.main()