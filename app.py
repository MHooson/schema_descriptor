"""
Main application module for the Schema Descriptor application.
Implements the Streamlit UI and application logic.
"""

import streamlit as st
import datetime
from config import config
from errors import SchemaDescriptorError, AuthenticationError, BigQueryError, LLMError
from services.auth_service import AuthService
from services.bigquery_service import BigQueryService
from services.llm_service import LLMService
from services.data_dictionary_service import DataDictionaryService
from utils.progress_utils import get_completion_percentage

def initialize_session_state():
    """Initialize session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "service_account_key" not in st.session_state:
        st.session_state.service_account_key = None
    if "gcp_credentials" not in st.session_state:
        st.session_state.gcp_credentials = None
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = None
    if "data_dict" not in st.session_state:
        st.session_state.data_dict = None
    if "has_data_dict" not in st.session_state:
        st.session_state.has_data_dict = False
    if "run_data_descriptions" not in st.session_state:
        st.session_state.run_data_descriptions = False
    if "run_commit_changes" not in st.session_state:
        st.session_state.run_commit_changes = False
    if "changes_committed" not in st.session_state:
        st.session_state.changes_committed = False
    if "services" not in st.session_state:
        st.session_state.services = {
            "auth": AuthService(),
            "bigquery": BigQueryService(),
            "llm": LLMService(),
            "data_dictionary": None
        }
    
    # Update has_data_dict flag for UI consistency
    if st.session_state.data_dict is not None:
        st.session_state.has_data_dict = True
    
    # Debug section - uncomment to see all session state variables
    # st.sidebar.write("Session State:", st.session_state)
        
def initialize_services():
    """Initialize application services."""
    # Set up LLM service with API key
    if st.session_state.openai_api_key:
        st.session_state.services["llm"] = LLMService(api_key=st.session_state.openai_api_key)
        
    # Set up BigQuery service with credentials
    if st.session_state.gcp_credentials:
        st.session_state.services["bigquery"] = BigQueryService(credentials=st.session_state.gcp_credentials)
        
    # Set up Data Dictionary service
    bq_service = st.session_state.services["bigquery"]
    llm_service = st.session_state.services["llm"]
    st.session_state.services["data_dictionary"] = DataDictionaryService(bq_service, llm_service)

def draw_sidebar():
    """Draw the application sidebar."""
    with st.sidebar:
        with st.columns(3)[1]:
            st.image(config.app_logo, width=90)
        st.title(config.app_title)
        st.write(config.app_description)
        
        # OpenAI API Key input
        st.header("OpenAI API Configuration")
        openai_api_key = st.text_input("OpenAI API Key", type="password")
        if openai_api_key:
            st.session_state.openai_api_key = openai_api_key
            initialize_services()
        
        # Authentication section
        st.header("Google Cloud Authentication")
        auth_method = st.radio("Authentication Method", ["Service Account Key"], index=0)
        
        if auth_method == "Service Account Key":
            uploaded_file = st.file_uploader("Upload Service Account Key (JSON)", type="json")
            if uploaded_file:
                key_content = uploaded_file.getvalue().decode("utf-8")
                st.session_state.service_account_key = key_content
                
                try:
                    auth_service = st.session_state.services["auth"]
                    credentials = auth_service.authenticate_gcp(service_account_key=key_content)
                    st.session_state.gcp_credentials = credentials
                    st.session_state.authenticated = True
                    initialize_services()
                    st.success("✓ Successfully authenticated with Google Cloud")
                except AuthenticationError as e:
                    st.error(f"Authentication failed: {e.message}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
        
        if not st.session_state.authenticated:
            st.warning("Please authenticate with Google Cloud to use this application")
        elif not st.session_state.openai_api_key:
            st.warning("Please provide an OpenAI API key to use this application")
        
        # Display inputs only if authenticated and API key is provided
        if st.session_state.authenticated and st.session_state.openai_api_key:
            # User inputs
            st.header("Dataset Configuration")
            
            project_id = st.text_input("Project ID", placeholder=config.default_project_id)
            st.session_state.project_id = project_id
            
            dataset_id = st.text_input("Dataset ID", placeholder=config.default_dataset_id)
            st.session_state.dataset_id = dataset_id
            
            limit_per_table = st.number_input("Number of rows to sample per table", 
                                            min_value=1, max_value=100, value=config.default_row_limit)
            st.session_state.limit_per_table = limit_per_table
            
            user_instructions = st.text_area("Additional LLM Instructions", value="", height=100)
            st.session_state.user_instructions = user_instructions

            # Date selectors for the partition filter
            start_date = st.date_input("Start Date", value=datetime.date.today() - datetime.timedelta(days=7))
            st.session_state.start_date = start_date
            
            end_date = st.date_input("End Date", value=datetime.date.today())
            st.session_state.end_date = end_date
            
            
            # Action buttons
            st.header("Actions")
            
            # Check Cost button
            if st.button("Check Cost", key="sidebar_check_cost"):
                with st.spinner("Estimating cost..."):
                    try:
                        total_bytes, cost_estimate = check_cost(
                            project_id=project_id,
                            dataset_id=dataset_id,
                            limit_per_table=limit_per_table,
                            start_date=start_date.isoformat(),
                            end_date=end_date.isoformat()
                        )
                        st.success(f"Estimated cost: ${cost_estimate:.2f} USD (Total: {total_bytes:.4f} GB)")
                    except BigQueryError as e:
                        st.error(f"Error estimating cost: {e.message}")
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {str(e)}")
            
            # Create data descriptions button
            if st.button("Create Data Descriptions", key="sidebar_create_descriptions"):
                st.session_state.run_data_descriptions = True
                st.experimental_rerun()  # Force a rerun to avoid password prompt
                
            # We'll create a custom container for the commit section
            commit_container = st.container()
            
            # Commit Changes button with appropriate status indicators
            with commit_container:
                # First check if we already committed changes
                if st.session_state.changes_committed:
                    st.success("✅ Changes committed successfully!")
                    # Use a click handler to avoid form submission behavior
                    if st.button("Commit Changes Again", key="sidebar_commit_changes"):
                        if st.session_state.has_data_dict:
                            # Set a session state flag instead of immediate action
                            st.session_state.run_commit_changes = True
                            st.experimental_rerun()  # Force a rerun to avoid password prompt
                        else:
                            st.error("No data descriptions to commit!")
                else:
                    # Add a small form key to isolate this button from other forms
                    if st.button("Commit Changes to BigQuery", key="sidebar_commit_changes"):
                        if st.session_state.has_data_dict:
                            # Set a session state flag instead of immediate action
                            st.session_state.run_commit_changes = True
                            st.experimental_rerun()  # Force a rerun to avoid password prompt
                        else:
                            st.error("No data descriptions to commit! Please generate data descriptions first.")
                
            # Show status of data dictionary
            if st.session_state.has_data_dict:
                st.success("✓ Data descriptions are ready")
            else:
                st.info("Generate data descriptions first")

def check_cost(project_id, dataset_id, limit_per_table, start_date, end_date):
    """
    Check the cost of building a data dictionary.
    
    Args:
        project_id: Google Cloud project ID
        dataset_id: BigQuery dataset ID
        limit_per_table: Maximum number of rows to sample per table
        start_date: Start date for partition filter
        end_date: End date for partition filter
        
    Returns:
        Tuple of (total_gb, cost_estimate)
    """
    bq_service = st.session_state.services["bigquery"]
    bq_service.project_id = project_id
    return bq_service.estimate_total_run_cost(dataset_id, limit_per_table, start_date, end_date)

def build_data_dictionary(project_id, dataset_id, instructions, limit_per_table, start_date, end_date, progress_callback):
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
    """
    data_dict_service = st.session_state.services["data_dictionary"]
    
    # Set sequential processing (simpler and more reliable)
    config.max_parallel_tables = 1
    config.batch_size = 10
    
    # Log settings
    print(f"Building dictionary with sequential processing")
    
    return data_dict_service.build_data_dictionary(
        project_id=project_id,
        dataset_id=dataset_id,
        instructions=instructions,
        limit_per_table=limit_per_table,
        start_date=start_date,
        end_date=end_date,
        progress_callback=progress_callback
    )

def update_bigquery_metadata(data_dict, project_id, dataset_id, progress_callback):
    """
    Update BigQuery metadata with data dictionary descriptions.
    
    Args:
        data_dict: Data dictionary
        project_id: Google Cloud project ID
        dataset_id: BigQuery dataset ID
        progress_callback: Function to call with progress updates
    """
    data_dict_service = st.session_state.services["data_dictionary"]
    data_dict_service.update_dataset_and_tables(
        data_dictionary=data_dict,
        project_id=project_id,
        dataset_id=dataset_id,
        progress_callback=progress_callback
    )

def draw_main_content():
    """Draw the main application content."""
    # Check if we should run data descriptions generation
    if st.session_state.run_data_descriptions:
        # Get input values from session state
        project_id = st.session_state.get("project_id", config.default_project_id)
        dataset_id = st.session_state.get("dataset_id", config.default_dataset_id)
        limit_per_table = st.session_state.get("limit_per_table", config.default_row_limit)
        user_instructions = st.session_state.get("user_instructions", "")
        start_date = st.session_state.get("start_date", datetime.date.today() - datetime.timedelta(days=7))
        end_date = st.session_state.get("end_date", datetime.date.today())
        
        # Create a status container
        status_container = st.empty()
        status_container.info("Starting data description generation...")
        
        # Create progress bar
        progress_bar = st.progress(0)
        
        # Track progress state
        progress_state = {"current_table": 0, "total_tables": 0, "stage": "initializing"}
        
        # Function to update status
        def update_status(message):
            status_container.info(message)
            print(message)  # Also log to console for debugging
            
            # Update progress bar based on message content
            if "Found" in message and "tables" in message:
                # Extract total tables
                try:
                    progress_state["total_tables"] = int(message.split(" ")[1])
                    progress_state["stage"] = "counting"
                    progress_bar.progress(5)  # Initial progress after counting
                except:
                    pass
            elif "Processing table" in message:
                # Extract current table
                try:
                    parts = message.split(" ")[2].split("/")
                    progress_state["current_table"] = int(parts[0])
                    progress_state["stage"] = "processing"
                    # Calculate progress: 10% for setup + 85% for tables + 5% for dataset
                    tables_progress = 85 * (progress_state["current_table"] / progress_state["total_tables"])
                    progress_bar.progress(int(10 + tables_progress))
                except:
                    pass
            elif "Generating dataset description" in message:
                progress_state["stage"] = "finalizing"
                progress_bar.progress(95)  # Almost done
            elif "complete" in message:
                progress_bar.progress(100)  # Done!
        
        try:
            # Call build_data_dictionary with progress callback
            result_dict = build_data_dictionary(
                project_id=project_id,
                dataset_id=dataset_id,
                instructions=user_instructions,
                limit_per_table=limit_per_table,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                progress_callback=update_status
            )
            
            # Extra validation for debug purposes
            print(f"DEBUG: Dictionary returned from build: type={type(result_dict)}, keys={list(result_dict.keys() if result_dict else [])}")
            
            # Ensure we have a dictionary before setting session state
            if result_dict is not None and isinstance(result_dict, dict):
                st.session_state.data_dict = result_dict
            else:
                status_container.error("Error: Invalid data dictionary returned")
                st.session_state.data_dict = {"_dataset_description": "Error occurred during generation"}
            
            # Update progress to complete
            progress_bar.progress(100)
            # Check if we have tables before showing success
            table_ids = [k for k in st.session_state.data_dict.keys() if k != "_dataset_description"]
            if len(table_ids) > 0:
                status_container.success(f"Data descriptions created for {len(table_ids)} tables!")
            else:
                status_container.warning("Dataset description created, but no table descriptions were generated. Check BigQuery permissions.")
            
            # Set flag that we have data descriptions if we have tables
            table_ids = [k for k in st.session_state.data_dict.keys() if k != "_dataset_description"]
            if len(table_ids) > 0:
                st.session_state.has_data_dict = True
                print(f"Setting has_data_dict=True because we have {len(table_ids)} tables")
            else:
                st.session_state.has_data_dict = False
                print(f"Setting has_data_dict=False because we have 0 tables")
                status_container.warning("No table descriptions were generated. There might be a BigQuery access issue.")
        except BigQueryError as e:
            status_container.error(f"BigQuery error: {e.message}")
            st.session_state.has_data_dict = False
        except LLMError as e:
            status_container.error(f"LLM error: {e.message}")
            st.session_state.has_data_dict = False
        except Exception as e:
            status_container.error(f"Error creating descriptions: {str(e)}")
            st.session_state.has_data_dict = False
            
        # Reset the flag
        st.session_state.run_data_descriptions = False
    
    # Show data dictionary output in the main window
    if st.session_state.data_dict is not None:
        data_dict = st.session_state.data_dict
        
        # Debug info
        table_keys = list(data_dict.keys())
        print(f"DISPLAY DEBUG: Data dict keys: {table_keys}")
        print(f"DISPLAY DEBUG: Data dict type: {type(data_dict)}")
        
        # Create a copy to avoid mutation problems
        display_dict = dict(data_dict)
        
        ds_desc = display_dict.get("_dataset_description", "")
        st.subheader("Dataset Description")
        updated_ds_desc = st.text_area("Edit Dataset Description", ds_desc)
        display_dict["_dataset_description"] = updated_ds_desc
        
        # Update original as well
        data_dict["_dataset_description"] = updated_ds_desc

        table_ids = [t for t in display_dict if t != "_dataset_description"]
        print(f"DISPLAY DEBUG: Table IDs to display: {table_ids}")
        
        # Show table count for debugging
        st.write(f"Found {len(table_ids)} tables to display")
        
        if not table_ids:
            st.warning("No tables were found with descriptions. This may indicate a processing error.")
        for table_id in table_ids:
            table_info = data_dict[table_id]
            st.markdown(f"### Table: `{table_id}`")
            table_desc = table_info.get("table_description", "")
            updated_table_desc = st.text_area(f"Table Description for {table_id}", table_desc)
            table_info["table_description"] = updated_table_desc
            columns = table_info.get("columns", {})
            if columns:
                for col_name, col_info in columns.items():
                    st.write(f"**Column:** {col_name}")
                    sample_values_str = ", ".join(str(v) for v in col_info["sample_values"][:5])
                    st.write(f"Sample Values: {sample_values_str}")
                    col_desc = col_info.get("llm_description", "")
                    updated_col_desc = st.text_area(f"Description for {table_id}.{col_name}", col_desc, key=f"{table_id}-{col_name}")
                    col_info["llm_description"] = updated_col_desc
            else:
                st.write("No columns found.")

        # Commit Changes button action
        if st.session_state.run_commit_changes and st.session_state.authenticated:
            # Get input values from session state
            project_id = st.session_state.get("project_id", config.default_project_id)
            dataset_id = st.session_state.get("dataset_id", config.default_dataset_id)
            
            # Create a status container
            commit_status = st.empty()
            commit_status.info("Starting update to BigQuery metadata...")
            
            # Create progress bar
            commit_progress = st.progress(0)
            
            # Function to update commit status
            def update_commit_status(message):
                commit_status.info(message)
                print(f"Commit status: {message}")
                
                # Update progress bar based on message content
                if "Updating table" in message:
                    try:
                        parts = message.split(" ")[2].split("/")
                        current = int(parts[0])
                        total = int(parts[1].split(":")[0])
                        progress_pct = get_completion_percentage(current, total)
                        commit_progress.progress(progress_pct)
                    except Exception as e:
                        print(f"Error parsing commit progress: {e}")
                elif "All updates" in message:
                    commit_progress.progress(100)
                    commit_status.success("Dataset and table descriptions updated successfully!")
            
            try:
                update_bigquery_metadata(
                    data_dict=data_dict,
                    project_id=project_id,
                    dataset_id=dataset_id,
                    progress_callback=update_commit_status
                )
                # Set flag that changes were committed
                st.session_state.changes_committed = True
            except BigQueryError as e:
                commit_status.error(f"BigQuery error: {e.message}")
                st.session_state.changes_committed = False
            except Exception as e:
                commit_status.error(f"Error updating BigQuery metadata: {str(e)}")
                st.session_state.changes_committed = False
                
            # Reset the flag
            st.session_state.run_commit_changes = False

def main():
    """Main application entry point."""
    st.set_page_config(
        page_title=config.app_title,
        page_icon="📊",
        layout="wide"
    )
    
    initialize_session_state()
    draw_sidebar()
    draw_main_content()

if __name__ == "__main__":
    main()