"""
Configuration module for the Schema Descriptor application.
Centralizes all configuration parameters and provides a consistent interface.
"""

import os

# LLM Configuration
DEFAULT_LLM_MODEL = "gpt-3.5-turbo"
DEFAULT_MAX_TOKENS = 80
DEFAULT_TEMPERATURE = 0.3

# BigQuery Configuration
DEFAULT_ROW_LIMIT = 5
DEFAULT_PROJECT_ID = "Enter your project here"
DEFAULT_DATASET_ID = "Enter your dataset here"

# Cache Configuration
CACHE_ENABLED = True

# Performance Configuration
BATCH_SIZE = 10       # Number of columns to process in a batch
MAX_PARALLEL_TABLES = 1  # Process tables sequentially for reliability
CACHE_EXPIRY_DAYS = 30  # Number of days before cache entries expire

# Application Configuration
APP_TITLE = "Data Description Builder with Brian"
APP_DESCRIPTION = "This app uses a script to query BigQuery tables, sample data, and generate descriptions using Brian."
APP_LOGO = 'brian_measurelab_logo.png'
APP_SECOND_LOGO = 'Measurelab Logo.svg'  # Using the same logo for now, replace with your second logo file

class Config:
    """
    Configuration class that manages all application settings.
    Can be initialized from environment variables or passed parameters.
    """
    
    def __init__(self):
        # LLM settings
        self.llm_model = os.environ.get("LLM_MODEL", DEFAULT_LLM_MODEL)
        self.llm_max_tokens = int(os.environ.get("LLM_MAX_TOKENS", DEFAULT_MAX_TOKENS))
        self.llm_temperature = float(os.environ.get("LLM_TEMPERATURE", DEFAULT_TEMPERATURE))
        
        # BigQuery settings
        self.default_project_id = os.environ.get("DEFAULT_PROJECT_ID", DEFAULT_PROJECT_ID)
        self.default_dataset_id = os.environ.get("DEFAULT_DATASET_ID", DEFAULT_DATASET_ID)
        self.default_row_limit = int(os.environ.get("DEFAULT_ROW_LIMIT", DEFAULT_ROW_LIMIT))
        
        # App settings
        self.app_title = APP_TITLE
        self.app_description = APP_DESCRIPTION
        self.app_logo = APP_LOGO
        self.app_second_logo = APP_SECOND_LOGO
        
        # Cache settings
        self.cache_enabled = CACHE_ENABLED
        
        # Performance settings - hardcoded for reliability
        self.batch_size = BATCH_SIZE
        self.max_parallel_tables = MAX_PARALLEL_TABLES
        self.cache_expiry_days = CACHE_EXPIRY_DAYS

# Create a singleton instance
config = Config()