"""
LLM service for the Schema Descriptor application.
Provides an abstraction for interacting with language models.
"""

import openai
import json
import datetime
from errors import LLMError
from utils.text_utils import _serialize_unknown_type
from config import config

class LLMService:
    """
    Service for interacting with language models.
    """
    
    def __init__(self, api_key=None, model=None, max_tokens=None, temperature=None):
        """
        Initialize a new LLM service.
        
        Args:
            api_key: API key for the LLM provider
            model: Name of the model to use
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation
        """
        self.api_key = api_key
        self.model = model or config.llm_model
        self.max_tokens = max_tokens or config.llm_max_tokens
        self.temperature = temperature or config.llm_temperature
        # Enhanced cache with timestamps for expiry checking
        self.cache = {}  # Format: {prompt: {"text": response_text, "timestamp": datetime}}
        
    def generate_text(self, prompt, max_retries=5, retry_delay=2):
        """
        Generate text from a prompt with retry logic.
        
        Args:
            prompt: The prompt to generate from
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Generated text
            
        Raises:
            LLMError: If the LLM request fails after all retries
        """
        import time
        
        # Check cache first with expiry
        if prompt in self.cache and self.cache[prompt] is not None:
            cache_entry = self.cache[prompt]
            
            # Handle both old string-only cache and new dict-based cache
            if isinstance(cache_entry, dict):
                cached_response = cache_entry["text"]
                timestamp = cache_entry["timestamp"]
                
                # Check if cache has expired
                if (datetime.datetime.now() - timestamp).days > config.cache_expiry_days:
                    print(f"Cache expired after {config.cache_expiry_days} days")
                else:
                    if not cached_response.startswith("Column containing") and not cached_response.startswith("Table containing") and not cached_response.startswith("Dataset containing"):
                        print(f"Using valid cached response (timestamp: {timestamp})")
                        return cached_response
            else:
                # Handle legacy cache format (string only)
                cached_response = cache_entry
                if not cached_response.startswith("Column containing") and not cached_response.startswith("Table containing") and not cached_response.startswith("Dataset containing"):
                    return cached_response
            
        if not self.api_key:
            raise LLMError(message="No API key provided", operation="text generation")
            
        # Set the API key for this request
        openai.api_key = self.api_key
        
        # Attempt with retries
        attempts = 0
        last_error = None
        
        while attempts < max_retries:
            try:
                print(f"Attempt {attempts + 1} for LLM call...")
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                description = response["choices"][0]["message"]["content"].strip()
                # Only cache non-empty, meaningful responses with timestamp
                if description and len(description) > 10:
                    self.cache[prompt] = {
                        "text": description,
                        "timestamp": datetime.datetime.now()
                    }
                print(f"LLM call successful, got {len(description)} characters")
                return description
            except Exception as e:
                attempts += 1
                last_error = e
                
                # Check if this is a server error (5xx) or rate limit error
                retry_error = False
                error_str = str(e)
                
                if "502 Bad Gateway" in error_str or "503 Service Unavailable" in error_str:
                    retry_error = True
                elif "429 Too Many Requests" in error_str:
                    retry_error = True
                elif "500 Internal Server Error" in error_str:
                    retry_error = True
                elif "timeout" in error_str.lower():
                    retry_error = True
                elif "connection" in error_str.lower():
                    retry_error = True
                    
                if retry_error and attempts < max_retries:
                    # Wait before retrying (exponential backoff)
                    wait_time = retry_delay * (2 ** (attempts - 1))
                    print(f"LLM API error: {error_str}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                # If we've exhausted retries or it's not a retryable error, raise the exception
                break
                
        # If we got here, all retries failed
        error_message = f"Failed to generate text after {max_retries} attempts"
        raise LLMError(message=error_message, operation="text generation", details=str(last_error))
        
    def generate_text_safely(self, prompt, default_text="Unable to generate description"):
        """
        Generate text with a fallback if generation fails.
        
        Args:
            prompt: The prompt to generate from
            default_text: Text to return if generation fails
            
        Returns:
            Generated text or default text on failure
        """
        # First check for existing cached result with expiry check
        if prompt in self.cache and self.cache[prompt] is not None:
            cache_entry = self.cache[prompt]
            
            # Handle both old string-only cache and new dict-based cache
            if isinstance(cache_entry, dict):
                cached_response = cache_entry["text"]
                timestamp = cache_entry["timestamp"]
                
                # Check if cache has expired
                if (datetime.datetime.now() - timestamp).days > config.cache_expiry_days:
                    print(f"Cache expired after {config.cache_expiry_days} days")
                else:
                    if not cached_response.startswith("Column containing") and not cached_response.startswith("Table containing") and not cached_response.startswith("Dataset containing"):
                        print(f"Using valid cached response: {cached_response[:20]}... (from {timestamp})")
                        return cached_response
            else:
                # Handle legacy cache format (string only)
                cached_response = cache_entry
                if not cached_response.startswith("Column containing") and not cached_response.startswith("Table containing") and not cached_response.startswith("Dataset containing"):
                    print(f"Using valid cached response: {cached_response[:20]}...")
                    return cached_response
        
        # Try multiple models if the primary model fails
        models_to_try = [self.model]
        
        # Only add fallback models if primary is GPT-3.5
        if self.model == "gpt-3.5-turbo":
            models_to_try.append("gpt-3.5-turbo-instruct")
            
        for model in models_to_try:
            try:
                current_model = self.model
                self.model = model
                result = self.generate_text(prompt)
                self.model = current_model
                
                # Check if we got a meaningful response
                if result and len(result) > 15 and not result.startswith("I'm sorry"):
                    print(f"Got good response from model {model}")
                    return result
            except Exception as e:
                print(f"Error generating text with model {model}: {e}")
        
        # None of the models worked, use default text but make it more informative
        if "column named" in prompt.lower():
            # Extract column name from prompt
            try:
                col_name = prompt.split("column named '")[1].split("'")[0]
                # Make a more informed default using the column name
                if "id" in col_name.lower() or "key" in col_name.lower():
                    return f"Unique identifier for {col_name.replace('_id', '').replace('_key', '')}"
                elif "date" in col_name.lower() or "time" in col_name.lower():
                    return f"Timestamp indicating when the {col_name.replace('_date', '').replace('_time', '')} occurred"
                elif "name" in col_name.lower():
                    return f"Name of the {col_name.replace('_name', '')}"
                else:
                    words = col_name.replace('_', ' ').title()
                    return f"{words} information for this record"
            except:
                pass
                
        print(f"Using default fallback text: {default_text}")
        return default_text

    def mask_sample_value(self, value):
        """
        Mask/format a sample value for inclusion in a prompt.
        
        Args:
            value: The value to mask
            
        Returns:
            Masked/formatted value
        """
        if value is None:
            return "NULL"
            
        if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
            return value.isoformat()
            
        if isinstance(value, (int, float)):
            return value
            
        if isinstance(value, str):
            return value[:10] + "..." if len(value) > 10 else value
            
        try:
            serialized = json.dumps(value, default=_serialize_unknown_type)
            return serialized[:50] + "..." if len(serialized) > 50 else serialized
        except Exception:
            string_val = str(value)
            return string_val[:50] + "..." if len(string_val) > 50 else string_val
            
    def get_column_description(self, table_id, column_name, sample_values, instructions=""):
        """
        Generate a description for a column.
        
        Args:
            table_id: ID of the table
            column_name: Name of the column
            sample_values: Sample values from the column
            instructions: Additional instructions for the LLM
            
        Returns:
            Generated description
        """
        masked_samples = [self.mask_sample_value(v) for v in sample_values]
        sample_str = ", ".join(str(v) for v in masked_samples[:5])
        
        prompt = (
            f"You are a data dictionary assistant. "
            f"I have a table called '{table_id}' with a column named '{column_name}'. "
            f"Sample data from this column includes: [{sample_str}]. "
            "Please provide a concise description of what this column represents. No need to include the table name."
            f"{instructions}"
        )
        
        return self.generate_text_safely(prompt, default_text=f"Column containing {column_name} data")
        
    def get_table_description(self, table_id, columns_and_samples, instructions=""):
        """
        Generate a description for a table.
        
        Args:
            table_id: ID of the table
            columns_and_samples: Dictionary of column names to sample values
            instructions: Additional instructions for the LLM
            
        Returns:
            Generated description
        """
        lines = []
        for col_name, samples in columns_and_samples.items():
            masked = [self.mask_sample_value(v) for v in samples[:3]]
            lines.append(f" - {col_name}: {masked}")
        columns_str = "\n".join(lines)
        
        prompt = (
            f"I have a table named '{table_id}'. Here are its columns and sample data:\n"
            f"{columns_str}\n\n"
            "Based on this, provide a concise, high-level description of what this table contains or represents."
            f"{instructions}"
        )
        
        return self.generate_text_safely(prompt, default_text=f"Table containing {table_id} data")
        
    def get_dataset_description(self, dataset_id, table_ids, instructions=""):
        """
        Generate a description for a dataset.
        
        Args:
            dataset_id: ID of the dataset
            table_ids: List of table IDs in the dataset
            instructions: Additional instructions for the LLM
            
        Returns:
            Generated description
        """
        truncated_tables = table_ids[:10]
        table_list_str = ", ".join(truncated_tables)
        
        prompt = (
            f"I have a dataset named '{dataset_id}' in BigQuery. It contains tables: {table_list_str} "
            "(possibly more). Please provide a concise, high-level description of the dataset."
            f"{instructions}"
        )
        
        return self.generate_text_safely(prompt, default_text=f"Dataset containing {dataset_id} data")