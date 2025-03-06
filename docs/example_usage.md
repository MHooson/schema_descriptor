# Example Usage

This guide demonstrates how to use Schema Descriptor to generate descriptions for BigQuery datasets.

## Prerequisites

Before you begin, make sure you have:

1. A Google Cloud service account with access to BigQuery
2. An OpenAI API key
3. Schema Descriptor installed and configured (see the [README.md](../README.md))

## Basic Usage

### Step 1: Start the application

```bash
streamlit run app.py
```

This will open the application in your web browser.

### Step 2: Configure Authentication

1. Enter your OpenAI API key in the sidebar
2. Upload your Google Cloud service account JSON key file
3. The application will verify your credentials

![Authentication Screenshot](images/auth_example.png)

### Step 3: Select Project and Dataset

1. Enter your Google Cloud project ID
2. Select a dataset from the dropdown menu
3. Verify that the tables are displayed correctly

### Step 4: Configure Sampling Parameters

1. Adjust the "Sample Size" slider to control how many rows to sample per table
2. If your tables are partitioned, set date filters to sample a specific range

![Configuration Screenshot](images/config_example.png)

### Step 5: Generate Descriptions

1. Click "Check Cost" to see an estimate of the BigQuery usage (optional)
2. Click "Create Data Descriptions" to start the process
3. Watch the progress indicators as the application:
   - Samples data from each table
   - Sends information to the LLM
   - Generates descriptions for the dataset, tables, and columns

![Generation Screenshot](images/generation_example.png)

### Step 6: Review and Edit

1. Review the automatically generated descriptions
2. Edit any descriptions that need improvement or correction
3. The editor supports markdown formatting for better readability

### Step 7: Save to BigQuery

1. When you're satisfied with the descriptions, click "Commit Changes to BigQuery"
2. The application will update your BigQuery metadata with the new descriptions
3. You'll see a confirmation message when complete

![Saving Screenshot](images/saving_example.png)

## Advanced Features

### Custom Instructions

You can provide custom instructions to the LLM by entering them in the "Additional Instructions" field. For example:

- "Focus on data governance aspects"
- "Highlight PII and sensitive data fields"
- "Use technical terminology appropriate for financial data"

### Error Handling

If you encounter errors:

1. Check the logs in the console where you started Streamlit
2. Verify that your service account has the correct permissions
3. For OpenAI API errors, check your rate limits and API key status

### Caching

The application caches LLM responses to save costs. If you want to regenerate descriptions:

1. Clear the cache by restarting the application
2. Or use the "Force Refresh" option if implemented

## Example Outputs

Below is an example of how your descriptions might look in BigQuery after using Schema Descriptor:

### Dataset Description

```
Sales Data Warehouse (SDW)

This dataset contains comprehensive sales transaction data from our e-commerce platform. It includes customer information, product details, orders, and shipping data from January 2020 to present.

The data is refreshed daily through an ETL process and is used for sales reporting, customer analysis, and inventory management.
```

### Table Description

```
Customer Orders Table

This table records all customer orders with associated metadata. Each row represents a unique order with details about the customer, timing, payment method, and order status.

The table is partitioned by order_date for efficient querying of specific time periods.
```

### Column Descriptions

```
- customer_id: Unique identifier for the customer who placed the order
- order_date: Timestamp when the order was placed (YYYY-MM-DD format)
- payment_method: Method used for payment (e.g., "credit_card", "paypal", "gift_card")
- order_total: Total monetary value of the order in USD, excluding tax and shipping
```

## Conclusion

Schema Descriptor makes it easy to maintain comprehensive, accurate documentation for your BigQuery resources with minimal manual effort.

For more details on the application's features and configuration options, refer to the [README.md](../README.md).