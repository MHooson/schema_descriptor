# Unit Tests for Schema Descriptor

This directory contains unit tests for the Schema Descriptor application.

## Running Tests

There are multiple ways to run the tests:

### Using run_tests.py

```bash
cd /path/to/schema_descriptor
python tests/run_tests.py
```

### Using pytest

```bash
cd /path/to/schema_descriptor
pip install -r requirements-test.txt
pytest
```

### Running specific test files

```bash
cd /path/to/schema_descriptor
python -m unittest tests/test_utility_functions.py
python -m unittest tests/test_llm_functions.py
python -m unittest tests/test_bigquery_functions.py
python -m unittest tests/test_main.py
```

## Test Coverage

To get a coverage report, run:

```bash
cd /path/to/schema_descriptor
pip install -r requirements-test.txt
pytest --cov=. --cov-report=html
```

This will generate an HTML coverage report in the `htmlcov` directory.