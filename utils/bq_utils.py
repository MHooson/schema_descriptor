"""
BigQuery utility functions.
Provides common functionality for working with BigQuery.
"""

import datetime
from google.cloud import bigquery

def handle_partition_filter(table, start_date=None, end_date=None):
    """
    Creates a partition filter clause for BigQuery queries based on table partitioning.
    
    Args:
        table: A BigQuery table object
        start_date: ISO formatted date string for the start date of the partition filter
        end_date: ISO formatted date string for the end date of the partition filter
        
    Returns:
        A string containing the WHERE clause for the partition filter, or an empty string if not applicable
    """
    partition_filter = ""
    if table.time_partitioning:
        # Use the partition field if specified; otherwise default to ingestion time.
        partition_field = table.time_partitioning.field or "_PARTITIONTIME"
        # If ingestion-time partitioning is in use, switch to the DATE pseudo column.
        if partition_field == "_PARTITIONTIME":
            partition_field = "_PARTITIONDATE"
        
        if start_date and end_date:
            partition_filter = f"WHERE `{partition_field}` BETWEEN '{start_date}' AND '{end_date}'"
        elif start_date:
            partition_filter = f"WHERE `{partition_field}` >= '{start_date}'"
        elif end_date:
            partition_filter = f"WHERE `{partition_field}` <= '{end_date}'"
        else:
            # If no dates are provided, default to today's date.
            today = datetime.date.today().isoformat()
            partition_filter = f"WHERE `{partition_field}` = '{today}'"
    
    return partition_filter

def flatten_column_dict(columns):
    """
    Flattens a nested column dictionary.
    
    Args:
        columns: A dictionary of column information
        
    Returns:
        A flattened dictionary
    """
    return {col_name: info for col_name, info in columns.items()}