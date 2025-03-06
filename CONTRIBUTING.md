# Contributing to Schema Descriptor

Thank you for your interest in contributing to Schema Descriptor! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Known Issues](#known-issues)

## Code of Conduct

Please be respectful and considerate when contributing to this project. Treat others as you would like to be treated.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Add the original repository as a remote named "upstream"
   ```
   git remote add upstream https://github.com/original/schema_descriptor.git
   ```
4. Create a new branch for your changes
   ```
   git checkout -b feature/your-feature-name
   ```

## Development Environment

### Setting Up

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies in the correct order:
   ```
   # Install key dependencies with specific versions first
   pip install protobuf==3.20.3
   pip install altair==4.2.2
   pip install streamlit==1.12.0
   pip install openai==0.28.0
   
   # Install remaining packages
   pip install -r requirements.txt --no-deps
   
   # Install test dependencies
   pip install -r requirements-test.txt
   ```

### Dependency Management

This project has strict dependency constraints:

- **protobuf**: Must be exactly 3.20.3 for compatibility with both Streamlit and Google libraries
- **altair**: Must be 4.2.2 for compatibility with Streamlit 1.12.0
- **streamlit**: Version 1.12.0 is used in this project
- **openai**: Version 0.28.0 is compatible with our API integration

If you need to add a new dependency, please verify it doesn't conflict with these constraints before submitting a PR.

## Making Changes

1. Make your changes in your feature branch
2. Follow the existing code style:
   - Use meaningful variable and function names
   - Add docstrings to functions
   - Follow PEP 8 guidelines
3. Keep changes focused on a single issue or feature

## Testing

Run the test suite before submitting changes:

```
python tests/run_tests.py
```

Note: Some tests may currently fail due to ongoing development. See the [Known Issues](#known-issues) section.

If you add new functionality, please also add appropriate tests.

## Pull Request Process

1. Update your fork to include the latest changes from upstream:
   ```
   git fetch upstream
   git merge upstream/main
   ```

2. Ensure your code passes the tests and linting

3. Create a pull request with:
   - A clear title
   - A description of the changes
   - Reference to any issues it addresses

4. Wait for review and be prepared to address feedback

## Known Issues

The following issues are currently known and being worked on:

1. **Test failures**: Several tests in the test suite are currently failing due to:
   - Mocking issues with BigQuery Service
   - LLM Service test inconsistencies

2. **Dependency conflicts**: The project has strict dependency requirements to maintain compatibility between Streamlit, BigQuery, and OpenAI libraries.

If you encounter these issues, please refer to this section before submitting a bug report.

Thank you for contributing!