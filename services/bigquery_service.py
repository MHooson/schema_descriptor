"""
BigQuery service for the Schema Descriptor application.
Provides an abstraction for interacting with BigQuery.
"""

import datetime
from google.cloud import bigquery
from errors import BigQueryError
from utils.bq_utils import handle_partition_filter, flatten_column_dict
from utils.text_utils import merge_descriptions

class BigQueryService:
    """
    Service for interacting with BigQuery.
    """
    
    def __init__(self, credentials=None, project_id=None):
        """
        Initialize a new BigQuery service.
        
        Args:
            credentials: Google Cloud credentials
            project_id: Google Cloud project ID
        """
        self.credentials = credentials
        self.project_id = project_id
        self.client = None
        
    def connect(self):
        """
        Connect to BigQuery.
        
        Returns:
            BigQuery client
            
        Raises:
            BigQueryError: If connection fails
        """
        try:
            print(f"DEBUG CONNECT: Connecting to BigQuery with project_id={self.project_id}")
            if not self.project_id:
                raise BigQueryError(message="No project_id specified for BigQuery connection")
                
            self.client = bigquery.Client(project=self.project_id, credentials=self.credentials)
            print(f"DEBUG CONNECT: Connection successful, client.project={self.client.project}")
            return self.client
        except Exception as e:
            print(f"DEBUG CONNECT: Connection failed: {str(e)}")
            raise BigQueryError(message="Failed to connect to BigQuery", details=str(e))
            
    def get_client(self):
        """
        Get the BigQuery client, connecting if necessary.
        
        Returns:
            BigQuery client
        """
        if not self.client:
            print(f"DEBUG: Creating new BigQuery client with project_id={self.project_id}")
            self.connect()
        elif self.client and self.client.project != self.project_id:
            print(f"DEBUG: Client project_id mismatch: client={self.client.project}, expected={self.project_id}. Reconnecting.")
            self.client = None
            self.connect()
            
        print(f"DEBUG: Using BigQuery client with project={self.client.project}")
        return self.client
        
    def list_tables(self, dataset_id):
        """
        List tables in a dataset.
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            List of table references
            
        Raises:
            BigQueryError: If listing tables fails
        """
        client = self.get_client()
        try:
            dataset_ref = client.dataset(dataset_id)
            return list(client.list_tables(dataset_ref))
        except Exception as e:
            raise BigQueryError(message="Failed to list tables", operation=f"listing tables in {dataset_id}", details=str(e))
            
    def get_table(self, table_id):
        """
        Get a table by ID.
        
        Args:
            table_id: ID of the table
            
        Returns:
            BigQuery table
            
        Raises:
            BigQueryError: If getting table fails
        """
        client = self.get_client()
        try:
            return client.get_table(table_id)
        except Exception as e:
            raise BigQueryError(message="Failed to get table", operation=f"getting table {table_id}", details=str(e))
            
    def sample_table_rows(self, table_id, limit=5, start_date=None, end_date=None):
        """
        Sample rows from a table.
        
        Args:
            table_id: ID of the table
            limit: Maximum number of rows to sample
            start_date: Start date for partition filter
            end_date: End date for partition filter
            
        Returns:
            List of sampled rows as dictionaries
            
        Raises:
            BigQueryError: If sampling fails
        """
        if not self.project_id:
            print(f"CRITICAL SAMPLE DEBUG: No project_id set for BigQueryService!")
        
        client = self.get_client()
        print(f"CRITICAL SAMPLE DEBUG: Using project_id={self.project_id} for sampling")
        
        try:
            print(f"CRITICAL SAMPLE DEBUG: Getting table {table_id}")
            table = self.get_table(table_id)
            print(f"CRITICAL SAMPLE DEBUG: Got table {table.table_id} in dataset {table.dataset_id}")
            
            partition_filter = handle_partition_filter(table, start_date, end_date)
            
            query = f"SELECT * FROM `{table_id}` {partition_filter} ORDER BY RAND() LIMIT {limit}"
            print(f"CRITICAL SAMPLE DEBUG: Executing query: {query}")
            
            query_job = client.query(query)
            results = list(query_job.result())
            
            rows_as_dict = [dict(row) for row in results]
            print(f"CRITICAL SAMPLE DEBUG: Got {len(rows_as_dict)} rows from {table_id}")
            
            # Sample validation
            if rows_as_dict and len(rows_as_dict) > 0:
                first_row = rows_as_dict[0]
                print(f"CRITICAL SAMPLE DEBUG: First row has {len(first_row.keys())} columns: {list(first_row.keys())[:5]}...")
            
            return rows_as_dict
        except Exception as e:
            print(f"CRITICAL SAMPLE DEBUG: Error sampling table {table_id}: {str(e)}")
            raise BigQueryError(message="Failed to sample table rows", operation=f"sampling {table_id}", details=str(e))
            
    def estimate_query_cost(self, table_id, limit=5, start_date=None, end_date=None):
        """
        Estimate the cost of a query.
        
        Args:
            table_id: ID of the table
            limit: Maximum number of rows to sample
            start_date: Start date for partition filter
            end_date: End date for partition filter
            
        Returns:
            Number of bytes processed
            
        Raises:
            BigQueryError: If cost estimation fails
        """
        client = self.get_client()
        try:
            table = self.get_table(table_id)
            partition_filter = handle_partition_filter(table, start_date, end_date)
            
            query = f"SELECT * FROM `{table_id}` {partition_filter} ORDER BY RAND() LIMIT {limit}"
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            query_job = client.query(query, job_config=job_config)
            return query_job.total_bytes_processed
        except Exception as e:
            raise BigQueryError(message="Failed to estimate query cost", operation=f"estimating cost for {table_id}", details=str(e))
            
    def estimate_total_run_cost(self, dataset_id, limit_per_table, start_date, end_date):
        """
        Estimate the total cost of running on all tables in a dataset.
        
        Args:
            dataset_id: ID of the dataset
            limit_per_table: Maximum number of rows to sample per table
            start_date: Start date for partition filter
            end_date: End date for partition filter
            
        Returns:
            Tuple of (total_gb, cost_estimate)
            
        Raises:
            BigQueryError: If cost estimation fails
        """
        total_bytes = 0
        tables = self.list_tables(dataset_id)
        
        for t in tables:
            fq_table_id = f"{t.project}.{t.dataset_id}.{t.table_id}"
            total_bytes += self.estimate_query_cost(fq_table_id, limit=limit_per_table, start_date=start_date, end_date=end_date)
            
        # BigQuery pricing is approximately $5 per TB processed.
        # 1 TB = 1e12 bytes.
        total_gb = total_bytes / 1e9
        cost_estimate = total_bytes / 1e12 * 5
        return total_gb, cost_estimate
        
    def update_schema_fields(self, fields, table_id, columns_dict, replace=True):
        """
        Update the schema fields of a table.
        
        Args:
            fields: List of schema fields
            table_id: ID of the table
            columns_dict: Dictionary of column descriptions
            replace: If True, replace existing descriptions; if False, merge them
            
        Returns:
            Updated list of schema fields
        """
        updated_fields = []
        for field in fields:
            field_path = field.name
            if field.field_type == "RECORD" and field.fields:
                subfields_updated = self.update_schema_fields(field.fields, table_id, columns_dict, replace)
                old_desc = field.description or ""
                new_desc = columns_dict.get(field_path, {}).get("llm_description") or ""
                final_desc = merge_descriptions(old_desc, new_desc, replace)
                
                updated_field = bigquery.SchemaField(
                    name=field.name,
                    field_type=field.field_type,
                    mode=field.mode,
                    description=final_desc,
                    fields=subfields_updated
                )
                updated_fields.append(updated_field)
            else:
                old_desc = field.description or ""
                new_desc = columns_dict.get(field_path, {}).get("llm_description") or ""
                final_desc = merge_descriptions(old_desc, new_desc, replace)
                
                updated_field = bigquery.SchemaField(
                    name=field.name,
                    field_type=field.field_type,
                    mode=field.mode,
                    description=final_desc,
                    fields=field.fields
                )
                updated_fields.append(updated_field)
                
        return updated_fields
        
    def update_dataset_and_tables(self, data_dictionary, dataset_id, progress_callback=None):
        """
        Update dataset and table descriptions in BigQuery.
        
        Args:
            data_dictionary: Dictionary of dataset and table descriptions
            dataset_id: ID of the dataset
            progress_callback: Function to call with progress updates
            
        Raises:
            BigQueryError: If update fails
        """
        client = self.get_client()
        dataset_ref = f"{self.project_id}.{dataset_id}"
        
        if progress_callback:
            progress_callback(f"Updating dataset {dataset_id} description")
            
        # Update dataset description
        ds_desc = data_dictionary.get("_dataset_description")
        if ds_desc:
            try:
                dataset = client.get_dataset(dataset_ref)
                old_desc = dataset.description or ""
                dataset.description = merge_descriptions(old_desc, ds_desc, replace=True)
                client.update_dataset(dataset, ["description"])
                
                if progress_callback:
                    progress_callback(f"Successfully updated dataset description")
            except Exception as e:
                error_msg = f"Error updating dataset description for {dataset_id}: {e}"
                if progress_callback:
                    progress_callback(error_msg)
                raise BigQueryError(message="Failed to update dataset description", operation=f"updating dataset {dataset_id}", details=str(e))
        
        # Count tables for progress tracking
        table_count = sum(1 for table_id in data_dictionary if table_id != "_dataset_description")
        current_table = 0
        
        # Update tables
        for table_id, table_info in data_dictionary.items():
            if table_id == "_dataset_description":
                continue
                
            current_table += 1
            if progress_callback:
                progress_callback(f"Updating table {current_table}/{table_count}: {table_id}")
                
            try:
                table = client.get_table(table_id)
                old_table_desc = table.description or ""
                new_table_desc = table_info.get("table_description", "")
                table.description = merge_descriptions(old_table_desc, new_table_desc, replace=True)
                
                columns_dict = flatten_column_dict(table_info["columns"])
                
                if progress_callback:
                    progress_callback(f"Updating schema for {table_id}")
                    
                updated_schema = self.update_schema_fields(table.schema, table_id, columns_dict, replace=True)
                table.schema = updated_schema
                client.update_table(table, ["description", "schema"])
                
                if progress_callback:
                    progress_callback(f"Successfully updated {table_id}")
            except Exception as e:
                error_msg = f"Error updating table {table_id}: {e}"
                if progress_callback:
                    progress_callback(error_msg)
                raise BigQueryError(message="Failed to update table", operation=f"updating table {table_id}", details=str(e))
                
        if progress_callback:
            progress_callback("All updates to BigQuery metadata complete")