import unittest
import sys
import os
from unittest.mock import MagicMock, patch
import datetime

from services.bigquery_service import BigQueryService
from errors import BigQueryError


class TestBigQueryService(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.bq_service = BigQueryService(project_id="test-project")
        self.bq_service._test_mode = True
    
    def test_init(self):
        """Test initialization."""
        service = BigQueryService(project_id="test-project")
        self.assertEqual(service.project_id, "test-project")
        self.assertIsNone(service.client)
    
    @patch('google.cloud.bigquery.Client')
    def test_connect_with_project(self, mock_client):
        """Test connect with project ID."""
        self.bq_service.project_id = "test-project"
        client = self.bq_service.connect()
        
        mock_client.assert_called_with(project="test-project", credentials=None)
        self.assertEqual(client, mock_client.return_value)
    
    @patch('google.cloud.bigquery.Client')
    def test_connect_error(self, mock_client):
        """Test connect with error."""
        mock_client.side_effect = Exception("API Error")
        
        with self.assertRaises(BigQueryError):
            self.bq_service.connect()
    
    def test_get_client_existing(self):
        """Test get_client with existing client."""
        mock_client = MagicMock()
        self.bq_service.client = mock_client
        
        result = self.bq_service.get_client()
        self.assertEqual(result, mock_client)
    
    @patch.object(BigQueryService, 'connect')
    def test_get_client_new_connection(self, mock_connect):
        """Test get_client with new connection."""
        mock_client = MagicMock()
        mock_connect.return_value = mock_client
        self.bq_service.client = None
        
        result = self.bq_service.get_client()
        self.assertEqual(result, mock_client)
        mock_connect.assert_called_once()
    
    @patch.object(BigQueryService, 'get_client')
    def test_list_datasets(self, mock_get_client):
        """Test list_datasets method."""
        # Mock client and dataset responses
        mock_client = MagicMock()
        mock_dataset1 = MagicMock()
        mock_dataset1.dataset_id = "dataset1"
        mock_dataset2 = MagicMock()
        mock_dataset2.dataset_id = "dataset2"
        
        mock_client.list_datasets.return_value = [mock_dataset1, mock_dataset2]
        mock_get_client.return_value = mock_client
        
        result = self.bq_service.list_datasets()
        self.assertEqual(result, ["dataset1", "dataset2"])
        mock_client.list_datasets.assert_called_once()
    
    @patch.object(BigQueryService, 'get_client')
    def test_list_datasets_error(self, mock_get_client):
        """Test list_datasets method with error."""
        mock_client = MagicMock()
        mock_client.list_datasets.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client
        
        with self.assertRaises(BigQueryError):
            self.bq_service.list_datasets()
    
    @patch.object(BigQueryService, 'get_client')
    def test_list_tables(self, mock_get_client):
        """Test list_tables method."""
        # Mock client and table responses
        mock_client = MagicMock()
        mock_table1 = MagicMock()
        mock_table1.table_id = "table1"
        mock_table2 = MagicMock()
        mock_table2.table_id = "table2"
        
        mock_client.list_tables.return_value = [mock_table1, mock_table2]
        mock_get_client.return_value = mock_client
        
        result = self.bq_service.list_tables("test_dataset")
        self.assertEqual(result, ["table1", "table2"])
        mock_client.list_tables.assert_called_once()
    
    @patch.object(BigQueryService, 'get_client')
    def test_list_tables_error(self, mock_get_client):
        """Test list_tables method with error."""
        mock_client = MagicMock()
        mock_client.list_tables.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client
        
        with self.assertRaises(BigQueryError):
            self.bq_service.list_tables("test_dataset")
    
    @patch.object(BigQueryService, 'get_client')
    def test_get_table(self, mock_get_client):
        """Test get_table method."""
        # Mock client and table response
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_table.table_id = "table1"
        
        mock_client.get_table.return_value = mock_table
        mock_get_client.return_value = mock_client
        
        result = self.bq_service.get_table("test_dataset.table1")
        self.assertEqual(result.table_id, "table1")
        mock_client.get_table.assert_called_once()
    
    @patch.object(BigQueryService, 'get_client')
    def test_get_table_error(self, mock_get_client):
        """Test get_table method with error."""
        mock_client = MagicMock()
        mock_client.get_table.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client
        
        with self.assertRaises(BigQueryError):
            self.bq_service.get_table("test_dataset.table1")


if __name__ == '__main__':
    unittest.main()