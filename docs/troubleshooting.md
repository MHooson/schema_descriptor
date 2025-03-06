# Troubleshooting Guide

This guide covers common issues you might encounter when using Schema Descriptor and how to resolve them.

## Installation Issues

### Dependency Errors

**Problem**: Error messages about incompatible dependency versions.

**Solution**: 
- Follow the exact order of installation in the [README.md](../README.md)
- Install key dependencies individually with their exact versions before others:
  ```
  pip install protobuf==3.20.3
  pip install altair==4.2.2
  pip install streamlit==1.12.0
  pip install openai==0.28.0
  ```
- Use `--no-deps` when installing the rest of the requirements

### ModuleNotFoundError: No module named 'altair.vegalite.v4'

**Problem**: This error occurs when Streamlit tries to use Altair features but the wrong version is installed.

**Solution**:
- Ensure you have exactly Altair 4.2.2 installed: `pip install altair==4.2.2`
- Reinstall Streamlit after installing Altair: `pip install streamlit==1.12.0`

### Import Errors with Google Cloud Libraries

**Problem**: Errors importing Google Cloud libraries or protobuf-related errors.

**Solution**:
- Check that protobuf version is exactly 3.20.3
- Check that the version of Google libraries match what's in requirements.txt
- Try uninstalling and reinstalling the Google libraries in order

## Authentication Issues

### Google Cloud Authentication Errors

**Problem**: "Failed to authenticate with Google Cloud" or similar errors.

**Solution**:
- Verify your service account key file is valid and not expired
- Ensure the service account has the necessary BigQuery permissions
- Check that you're using the correct project ID
- Try authenticating with gcloud CLI separately to verify credentials

### OpenAI API Errors

**Problem**: "Invalid API key" or "API key not found" errors.

**Solution**:
- Verify your OpenAI API key is valid and not expired
- Check if you've reached your API request limits
- Ensure you're using the right key type (e.g., not using a test key in production)

## Runtime Issues

### Timeout When Processing Large Datasets

**Problem**: The application times out or fails when processing large datasets.

**Solution**:
- Reduce the "Sample Size" parameter to sample fewer rows
- Use date filters to process a smaller time range
- Process tables individually instead of the entire dataset
- Check BigQuery query quotas in your Google Cloud project

### "Out of Memory" Errors

**Problem**: Streamlit crashes with memory-related errors.

**Solution**:
- Process fewer tables at once
- Reduce the "Maximum Parallel Tables" setting if available
- Restart the application to clear the cache
- Run Streamlit with more memory if possible

### LLM Response Errors

**Problem**: OpenAI returns errors or incomplete responses.

**Solution**:
- Check if responses exceed token limits
- Verify your OpenAI account has API access
- Review for any inappropriate content in your data samples
- Try reducing the complexity of data being sent to the API

## BigQuery Issues

### Permission Denied When Writing Metadata

**Problem**: Errors when trying to update BigQuery metadata.

**Solution**:
- Verify your service account has both read AND write permissions for BigQuery
- Check specifically for `bigquery.tables.update` permissions
- Ensure you're not trying to modify a dataset that's outside your project scope

### "Table Not Found" or "Dataset Not Found" Errors

**Problem**: BigQuery can't find the tables or datasets you're trying to access.

**Solution**:
- Check that the project ID and dataset ID are correct
- Verify the tables actually exist in the specified dataset
- Ensure your service account has access to the specific dataset
- Check for typos in table or dataset names

## Application Behavior Issues

### Progress Gets Stuck

**Problem**: The progress indicator stops moving during processing.

**Solution**:
- Check application logs for hidden errors
- For very large tables, the sampling process might take a long time
- Try refreshing the page or restarting the application
- Reduce the sample size for better performance

### Generated Descriptions Are Poor Quality

**Problem**: The LLM generates inaccurate or generic descriptions.

**Solution**:
- Increase the sample size to give the LLM more context
- Add specific instructions in the "Additional Instructions" field
- Manually review and edit descriptions before committing
- Check if sampling captured representative data from your tables

## Still Having Issues?

If you encounter problems not covered in this guide:

1. Check the console where you started the Streamlit application for detailed logs
2. Review the [DEPENDENCY_NOTES.md](../DEPENDENCY_NOTES.md) file for known issues
3. Submit an issue on the GitHub repository with:
   - A clear description of the problem
   - Steps to reproduce
   - Complete error messages and logs
   - Your environment details (Python version, OS, etc.)