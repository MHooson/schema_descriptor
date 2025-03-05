"""
Utility functions for the Schema Descriptor application.
Provides common functionality used across the application.
"""

# Import utility functions for easier access
from .bq_utils import handle_partition_filter
from .text_utils import merge_descriptions
from .progress_utils import get_completion_percentage