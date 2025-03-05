"""
Authentication service for the Schema Descriptor application.
Provides functionality for authenticating with Google Cloud Platform.
"""

import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from errors import AuthenticationError

class AuthService:
    """
    Service for authenticating with external services.
    """
    
    def __init__(self):
        """
        Initialize a new authentication service.
        """
        self.credentials = None
        
    def authenticate_gcp(self, service_account_key=None, credentials=None):
        """
        Authenticate with Google Cloud Platform.
        
        Args:
            service_account_key: Service account key JSON string
            credentials: Existing credentials object
            
        Returns:
            GCP credentials object
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Return existing credentials if they're valid
        if credentials:
            if not credentials.expired or credentials.refresh_token:
                try:
                    if credentials.expired:
                        credentials.refresh(Request())
                    self.credentials = credentials
                    return credentials
                except RefreshError as e:
                    raise AuthenticationError(message="Credentials expired", service="Google Cloud", details=str(e))
                except Exception as e:
                    raise AuthenticationError(message="Failed to use existing credentials", service="Google Cloud", details=str(e))
                    
        # Try to authenticate with service account key
        if service_account_key:
            try:
                key_json = json.loads(service_account_key)
                credentials = service_account.Credentials.from_service_account_info(key_json)
                self.credentials = credentials
                return credentials
            except json.JSONDecodeError as e:
                raise AuthenticationError(message="Invalid service account key format", service="Google Cloud", details="The service account key is not valid JSON")
            except Exception as e:
                raise AuthenticationError(message="Failed to authenticate with service account", service="Google Cloud", details=str(e))
                
        raise AuthenticationError(message="No valid authentication method provided", service="Google Cloud")