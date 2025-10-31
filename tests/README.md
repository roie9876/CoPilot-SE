# Tests

This directory contains the test suite for Co-Pilot SE.

## Structure

```
tests/
├── unit/           # Unit tests for individual functions/classes
├── integration/    # Integration tests for component interactions
├── e2e/            # End-to-end tests for full workflows
└── conftest.py     # Shared pytest fixtures (to be created)
```

## Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_agents.py
```

## Test Guidelines

See [CONTRIBUTING.md](../CONTRIBUTING.md#testing) for testing standards and conventions.

## Implementation Status

⚠️ **Phase 2**: Tests will be implemented during the POC development phase.
