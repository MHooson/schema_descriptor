# Dependency Management Notes

This document outlines known dependency constraints and issues in the Schema Descriptor project. It's intended for maintainers and contributors to understand the dependency landscape.

## Critical Dependencies

### Protobuf (3.20.3)

This project requires protobuf version 3.20.3 due to several conflicting constraints:

- Streamlit 1.12.0 requires protobuf < 4.0.0
- Google Cloud BigQuery libraries require protobuf >= 3.19.5
- gRPC-status requires protobuf >= 4.21.6 (which we've worked around)

Using any other version of protobuf will cause dependency conflicts:
- Lower versions won't work with Google Cloud libraries
- Higher versions (4.x) won't work with Streamlit

### Altair (4.2.2)

Altair must be exactly version 4.2.2 because:

- Streamlit 1.12.0 depends on the `altair.vegalite.v4` module
- Newer versions of Altair (>= 5.0.0) removed this module structure
- This causes `ModuleNotFoundError: No module named 'altair.vegalite.v4'` errors

### Streamlit (1.12.0)

The application is built with Streamlit 1.12.0. Upgrading to newer versions would:
- Require extensive refactoring
- Potentially solve some dependency issues
- But introduce backwards compatibility concerns

### OpenAI (0.28.0)

OpenAI version 0.28.0 is used because:
- It has a compatible API with our LLM service integration
- Newer client libraries (>=1.0.0) have completely different APIs

## Dependency Resolution Strategy

The following installation order helps resolve dependency conflicts:

1. Install protobuf first: `pip install protobuf==3.20.3`
2. Install Altair: `pip install altair==4.2.2`  
3. Install Streamlit: `pip install streamlit==1.12.0`
4. Install OpenAI: `pip install openai==0.28.0`
5. Install remaining dependencies: `pip install -r requirements.txt --no-deps`

## CI/CD Pipeline

In the GitHub Actions workflow:

1. We explicitly install test dependencies first
2. Then install key dependencies in the correct order
3. Use `--no-deps` to avoid dependency resolution issues
4. Skip tests that are known to fail due to dependency mocking issues

## Future Improvements

Potential improvements to dependency management:

1. **Upgrade Streamlit**: Moving to a newer version would resolve several issues but require code changes
2. **Use Docker**: Containerization would provide a more consistent environment
3. **Split Requirements**: Create separate requirement files for main, dev, and test dependencies
4. **Fix Test Mocks**: Update tests to work better with the current dependency constraints

## Known Dependency-Related Issues

1. **Test failures**: Some tests fail when mocking dependencies due to strict type checking
2. **Install errors**: Non-ordered installation may lead to dependency resolution failures
3. **Version control**: Pin exact versions vs compatible versions (`==` vs `~=`) trade-off