# Schema Descriptor

A streamlit application that automatically generates data descriptions for BigQuery datasets and tables using OpenAI's language models.

## Overview

Schema Descriptor helps data teams create and maintain comprehensive documentation for their BigQuery datasets by:

1. Sampling data from tables
2. Generating human-readable descriptions using LLMs
3. Writing the descriptions back to BigQuery metadata
4. Providing a user interface to review and edit descriptions before committing

## Features

- **Authentication**: Secure authentication with Google Cloud Platform using service account keys
- **Cost Estimation**: Calculate the cost of BigQuery operations before running them
- **Customisable Sampling**: Control the number of rows sampled from each table
- **Date Filtering**: Automatic partition detection, allowing for filtering of larger tables bay date
- **Interactive UI**: Edit generated descriptions before committing them to BigQuery
- **Caching**: LLM responses are cached to reduce API costs
- **Error Resilience**: Retry logic and fallback mechanisms for API failures
- **Progress Tracking**: Detailed progress information during long operations

## Installation

1. Clone the repository
2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies in the correct order (this is important due to dependency constraints):
   ```
   # Install key dependencies with specific versions first
   pip install protobuf==3.20.3
   pip install altair==4.2.2
   pip install streamlit==1.12.0
   pip install openai==0.28.0
   
   # Install remaining packages
   pip install -r requirements.txt --no-deps
   ```

### Dependency Constraints

This project has specific dependency requirements due to compatibility constraints:

- **protobuf**: Must be exactly 3.20.3 to work with both Streamlit and Google Cloud libraries
- **altair**: Must be 4.2.2 to work with Streamlit 1.12.0
- **streamlit**: Version 1.12.0 is required
- **openai**: Version 0.28.0 is required for the current API integration

Installing dependencies in a different order or with different versions may cause errors.

For detailed information about dependencies, see [DEPENDENCY_NOTES.md](DEPENDENCY_NOTES.md).

## Usage

1. Run the Streamlit application:
   ```
   streamlit run app.py
   ```

2. Enter your OpenAI API key in the sidebar

3. Upload your Google Cloud service account key (JSON file) in the sidebar

4. Enter your BigQuery project and dataset IDs

5. (Optional) Adjust sampling parameters and date filters

6. Click "Check Cost" to estimate the cost of your operation

7. Click "Create Data Descriptions" to generate descriptions for your dataset and tables

8. Review and edit the descriptions in the main window

9. Click "Commit Changes to BigQuery" to save the descriptions back to your BigQuery metadata

For more detailed instructions with screenshots, see [docs/example_usage.md](docs/example_usage.md).

If you run into issues, check the [docs/troubleshooting.md](docs/troubleshooting.md) guide.

## Project Structure

### Core Application
- `app.py`: Main Streamlit application and UI
- `config.py`: Configuration settings and environment variables
- `errors.py`: Custom exception classes for error handling

### Services
- `services/auth_service.py`: Authentication with Google Cloud
- `services/bigquery_service.py`: BigQuery operations and metadata management
- `services/llm_service.py`: Language model integration with error handling
- `services/data_dictionary_service.py`: Core business logic for data dictionaries

### Utilities
- `utils/bq_utils.py`: BigQuery utility functions
- `utils/text_utils.py`: Text processing utilities
- `utils/progress_utils.py`: Progress tracking and reporting

## Requirements

- Python 3.9+
- Google Cloud service account with BigQuery access
- OpenAI API key

## Security Note

This application requires access to your BigQuery data and uses OpenAI's API. Please ensure:

1. Your service account has appropriate permissions
2. You review generated descriptions before committing them to ensure no sensitive data is exposed

## Contributing

We welcome contributions to improve Schema Descriptor! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines and instructions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.