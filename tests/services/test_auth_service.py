import unittest
import sys
import os
from unittest.mock import MagicMock, patch

from services.auth_service import AuthService
from errors import AuthenticationError


class TestAuthService(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.auth_service = AuthService()
    
    @patch('google.oauth2.service_account.Credentials.from_service_account_info')
    def test_authenticate_gcp_with_service_account(self, mock_from_service_account_info):
        """Test authenticate_gcp with service account key."""
        # Mock service account credentials
        mock_credentials = MagicMock()
        mock_from_service_account_info.return_value = mock_credentials
        
        # Valid service account key JSON
        service_account_key = '{"type": "service_account", "project_id": "test-project"}'
        
        result = self.auth_service.authenticate_gcp(service_account_key=service_account_key)
        
        self.assertEqual(result, mock_credentials)
        mock_from_service_account_info.assert_called_once()
    
    def test_authenticate_gcp_with_existing_credentials(self):
        """Test authenticate_gcp with existing valid credentials."""
        # Mock credentials that are not expired
        mock_credentials = MagicMock()
        mock_credentials.expired = False
        
        result = self.auth_service.authenticate_gcp(credentials=mock_credentials)
        
        self.assertEqual(result, mock_credentials)
    
    def test_authenticate_gcp_with_expired_credentials(self):
        """Test authenticate_gcp with expired credentials that can be refreshed."""
        # Mock credentials that are expired but have a refresh token
        mock_credentials = MagicMock()
        mock_credentials.expired = True
        mock_credentials.refresh_token = True
        
        result = self.auth_service.authenticate_gcp(credentials=mock_credentials)
        
        self.assertEqual(result, mock_credentials)
        mock_credentials.refresh.assert_called_once()
    
    def test_authenticate_gcp_with_expired_credentials_error(self):
        """Test authenticate_gcp with expired credentials that fail to refresh."""
        # Mock credentials that are expired and fail to refresh
        mock_credentials = MagicMock()
        mock_credentials.expired = True
        mock_credentials.refresh_token = True
        mock_credentials.refresh.side_effect = Exception("Refresh error")
        
        with self.assertRaises(AuthenticationError):
            self.auth_service.authenticate_gcp(credentials=mock_credentials)
    
    def test_authenticate_gcp_no_auth_method(self):
        """Test authenticate_gcp with no authentication method."""
        with self.assertRaises(AuthenticationError):
            self.auth_service.authenticate_gcp()


if __name__ == '__main__':
    unittest.main()