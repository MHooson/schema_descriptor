"""
Data Dictionary service for the Schema Descriptor application.
Provides functionality for building and updating data dictionaries.
"""

import concurrent.futures
import math
import threading
from errors import SchemaDescriptorError
from utils.progress_utils import ProgressTracker
from config import config

class DataDictionaryService:
    """
    Service for building and updating data dictionaries.
    """
    
    def __init__(self, bq_service, llm_service):
        """
        Initialize a new data dictionary service.
        
        Args:
            bq_service: BigQuery service
            llm_service: LLM service
        """
        self.bq_service = bq_service
        self.llm_service = llm_service
        self.lock = threading.Lock()  # For thread-safe operations
        
    def process_table(self, table_id, project_id, limit_per_table, start_date, end_date, 
                   instructions, progress):
        """
        Process a single table for the data dictionary.
        
        Args:
            table_id: Fully qualified table ID
            project_id: Google Cloud project ID
            limit_per_table: Maximum number of rows to sample
            start_date: Start date for partition filter
            end_date: End date for partition filter
            instructions: Additional instructions for the LLM
            progress: Progress tracker object
            
        Returns:
            Tuple of (table_id, table_data) where table_data contains description and columns
        """
        # Ensure BigQuery service has the correct project ID set
        self.bq_service.project_id = project_id
        progress.update(f"Processing table: {table_id}")
        
        table_data = {
            "table_description": None,
            "columns": {}
        }
        
        # Sample rows from the table
        progress.update(f"Sampling data from {table_id}...")
        try:
            print(f"CRITICAL TABLE DEBUG: Trying to sample table {table_id} with project_id={self.bq_service.project_id}")
            rows = self.bq_service.sample_table_rows(table_id, limit_per_table, start_date, end_date)
            print(f"CRITICAL TABLE DEBUG: Got {len(rows)} rows from {table_id}")
        except Exception as e:
            print(f"CRITICAL TABLE DEBUG: Exception sampling table {table_id}: {str(e)}")
            progress.update(f"Error sampling table {table_id}: {str(e)}")
            return table_id, table_data
        
        if not rows:
            progress.update(f"No data found in {table_id}, skipping")
            return table_id, table_data
            
        # Process columns
        columns_info = {}
        try:
            col_names = rows[0].keys()
            
            for col_name in col_names:
                col_samples = [r.get(col_name, None) for r in rows]
                columns_info[col_name] = {
                    "sample_values": col_samples,
                    "llm_description": None
                }
        except IndexError:
            progress.update(f"Warning: No rows in sample for {table_id}")
            # Return empty table data if there are no rows
            return table_id, table_data
            
        # Generate descriptions using LLM in batches
        total_columns = len(columns_info)
        progress.update(f"Generating descriptions for {total_columns} columns in {table_id}...")
        
        # Process columns in batches for better performance
        batch_size = config.batch_size
        batches = math.ceil(total_columns / batch_size)
        
        # Convert columns_info to list for batch processing
        columns_list = list(columns_info.items())
        
        for batch_index in range(batches):
            start_idx = batch_index * batch_size
            end_idx = min(start_idx + batch_size, total_columns)
            batch = columns_list[start_idx:end_idx]
            
            progress.update(f"Processing batch {batch_index+1}/{batches} for {table_id}")
            
            # Process batch items
            for col_index, (col_name, info) in enumerate(batch):
                if total_columns > 5:
                    progress.update(f"Column {col_name} in {table_id}")
                
                try:
                    description = self.llm_service.get_column_description(
                        table_id, col_name, info["sample_values"], instructions
                    )
                    # Update the original columns_info dictionary
                    columns_info[col_name]["llm_description"] = description
                except Exception as e:
                    progress.update(f"Error generating description for column {col_name}: {str(e)}")
                    columns_info[col_name]["llm_description"] = f"Error: {str(e)[:100]}"
                
        # Generate table description
        progress.update(f"Generating table description for {table_id}...")
        try:
            table_prompt_data = {c: i["sample_values"] for c, i in columns_info.items()}
            table_desc = self.llm_service.get_table_description(table_id, table_prompt_data, instructions)
            table_data["table_description"] = table_desc
        except Exception as e:
            progress.update(f"Error generating table description: {str(e)}")
            table_data["table_description"] = f"Error generating description: {str(e)[:100]}"
        
        # Copy the columns info to the table data
        table_data["columns"] = columns_info
        
        progress.update(f"Completed processing table: {table_id}")
        return table_id, table_data
    
    def build_data_dictionary(self, project_id, dataset_id, instructions="", limit_per_table=5, 
                             start_date=None, end_date=None, progress_callback=None):
        """
        Build a data dictionary for a BigQuery dataset.
        
        Args:
            project_id: Google Cloud project ID
            dataset_id: BigQuery dataset ID
            instructions: Additional instructions for the LLM
            limit_per_table: Maximum number of rows to sample per table
            start_date: Start date for partition filter
            end_date: End date for partition filter
            progress_callback: Function to call with progress updates
            
        Returns:
            Data dictionary
            
        Raises:
            SchemaDescriptorError: If building the data dictionary fails
        """
        # Set the project ID for the BigQuery service
        self.bq_service.project_id = project_id
        
        # Create progress tracker
        progress = ProgressTracker(callback=progress_callback)
        
        # Build data dictionary
        data_dictionary = {}
        
        # List tables in the dataset
        try:
            tables = self.bq_service.list_tables(dataset_id)
            table_ids = [f"{t.project}.{t.dataset_id}.{t.table_id}" for t in tables]
            total_tables = len(table_ids)
            
            progress.update(f"Found {total_tables} tables in dataset {dataset_id}", total=total_tables)
        except Exception as e:
            error_msg = f"Error listing tables: {str(e)}"
            progress.update(error_msg)
            raise SchemaDescriptorError(message=error_msg, operation="listing tables")
        
        # Determine max workers (parallel tables)
        max_workers = min(config.max_parallel_tables, total_tables)
        
        if max_workers > 1 and total_tables > 1:
            progress.update(f"Processing {total_tables} tables with {max_workers} parallel workers")
            
            # Process tables in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tables for processing
                future_to_table = {
                    executor.submit(
                        self.process_table, 
                        table_id, 
                        project_id, 
                        limit_per_table, 
                        start_date, 
                        end_date, 
                        instructions, 
                        progress
                    ): table_id for table_id in table_ids
                }
                
                # Process results as they complete
                completed = 0
                for future in concurrent.futures.as_completed(future_to_table):
                    table_id = future_to_table[future]
                    completed += 1
                    
                    try:
                        processed_id, table_data = future.result()
                        with self.lock:
                            # Make sure we're not overwriting existing data
                            if processed_id in data_dictionary:
                                print(f"Warning: Table {processed_id} already exists in dictionary!")
                            data_dictionary[processed_id] = table_data
                            # For debugging
                            print(f"Added table {processed_id} with {len(table_data.get('columns', {}))} columns to dictionary")
                        progress.update(f"Completed table {completed}/{total_tables}: {table_id}", current=completed)
                    except Exception as e:
                        progress.update(f"Error processing table {table_id}: {str(e)}")
                        # Continue with other tables even if one fails
        else:
            # Process tables sequentially
            for table_index, table_id in enumerate(table_ids):
                current_table = table_index + 1
                progress.update(f"Processing table {current_table}/{total_tables}: {table_id}", current=current_table)
                
                try:
                    print(f"CRITICAL DEBUG: Starting process_table for {table_id}")
                    # Create a safe local copy of the BigQuery service with correct project ID
                    # This is to ensure project_id is properly set for each table
                    from google.cloud import bigquery
                    import copy
                    
                    # Set project ID directly in this thread
                    self.bq_service.project_id = project_id
                    
                    # Now process the table
                    processed_id, table_data = self.process_table(
                        table_id, 
                        project_id, 
                        limit_per_table, 
                        start_date, 
                        end_date, 
                        instructions, 
                        progress
                    )
                    print(f"CRITICAL DEBUG: Received result from process_table: {processed_id}, with data: {table_data.keys()}")
                    print(f"CRITICAL DEBUG: Table columns: {list(table_data.get('columns', {}).keys())}")
                    
                    # Store result in dictionary
                    data_dictionary[processed_id] = table_data
                    
                    # Verify storage succeeded
                    print(f"CRITICAL DEBUG: After adding to dictionary - keys: {list(data_dictionary.keys())}")
                    if processed_id in data_dictionary:
                        print(f"CRITICAL DEBUG: Table {processed_id} successfully added to dictionary")
                    else:
                        print(f"CRITICAL DEBUG: ERROR! Table {processed_id} NOT added to dictionary!")
                    
                    # For debugging
                    print(f"Sequential: Added table {processed_id} with {len(table_data.get('columns', {}))} columns to dictionary")
                except Exception as e:
                    print(f"CRITICAL DEBUG: Exception in process_table: {str(e)}")
                    progress.update(f"Error processing table {table_id}: {str(e)}")
                    # Continue with other tables even if one fails
        
        # Final validation check before returning
        print(f"FINAL DEBUG: Dictionary keys before adding dataset description: {list(data_dictionary.keys())}")
        
        # Generate dataset description
        if table_ids:
            progress.update(f"Generating dataset description for {dataset_id}...")
            try:
                ds_desc = self.llm_service.get_dataset_description(dataset_id, table_ids, instructions)
                data_dictionary["_dataset_description"] = ds_desc
            except Exception as e:
                progress.update(f"Error generating dataset description: {str(e)}")
                data_dictionary["_dataset_description"] = f"Error generating dataset description: {str(e)[:100]}"
        else:
            # Ensure we have a dataset description even if no tables
            data_dictionary["_dataset_description"] = f"Dataset {dataset_id} (no valid tables found)"
        
        # Additional validation
        if len(data_dictionary) <= 1 and "_dataset_description" in data_dictionary:
            progress.update("Warning: No table data was processed successfully!")
            
        progress.update("Data dictionary creation complete!")
        # Debug output
        print(f"Final data dictionary has {len(data_dictionary)} entries (including dataset description)") 
        for key in data_dictionary.keys():
            print(f"  - {key}")
            
        return data_dictionary
        
    def update_dataset_and_tables(self, data_dictionary, project_id, dataset_id, progress_callback=None):
        """
        Update dataset and table descriptions in BigQuery.
        
        Args:
            data_dictionary: Dictionary of dataset and table descriptions
            project_id: Google Cloud project ID
            dataset_id: BigQuery dataset ID
            progress_callback: Function to call with progress updates
            
        Raises:
            SchemaDescriptorError: If updating the dataset and tables fails
        """
        # Set the project ID for the BigQuery service
        self.bq_service.project_id = project_id
        
        # Update dataset and tables
        self.bq_service.update_dataset_and_tables(data_dictionary, dataset_id, progress_callback)