# Testing Guide for Co-Pilot SE

This guide explains how to run and write tests for the Co-Pilot SE project.

---

## 🚀 Quick Start

### 1. Install Dependencies

First, install the required testing packages:

```bash
# Install all dependencies including testing tools
pip install -r requirements.txt

# Or install just the testing dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock
```

### 2. Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=html

# Run and open coverage report in browser (macOS)
pytest --cov=src --cov-report=html && open htmlcov/index.html
```

### 3. Run Specific Tests

```bash
# Run tests for a specific file
pytest tests/test_requirements_agent.py

# Run a specific test class
pytest tests/test_requirements_agent.py::TestRequirementsAgent

# Run a specific test method
pytest tests/test_requirements_agent.py::TestRequirementsAgent::test_cloud_platform_detection

# Run tests matching a keyword
pytest -k "cloud_detection"

# Run tests with a specific marker
pytest -m unit
pytest -m azure
```

---

## 📊 Test Structure

### Current Test Files

```
tests/
├── __init__.py                      # Test package initialization
├── conftest.py                      # Shared fixtures and configuration
├── test_requirements_agent.py       # Requirements Agent tests (✅ COMPLETE)
├── test_architecture_agent.py       # Architecture Agent tests (TODO)
├── test_cost_agent.py              # Cost Agent tests (TODO)
├── test_documentation_agent.py     # Documentation Agent tests (TODO)
└── test_orchestrator.py            # Integration tests (TODO)
```

### Test Categories

Tests are organized by markers in `pytest.ini`:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, multiple components)
- `@pytest.mark.azure` - Azure-specific tests
- `@pytest.mark.aws` - AWS-specific tests
- `@pytest.mark.gcp` - GCP-specific tests
- `@pytest.mark.slow` - Tests that take longer to run

---

## 🧪 Writing Tests

### Test Structure

```python
import pytest
from src.agents.your_agent import YourAgent
from src.models.schemas import YourInput, YourOutput


class TestYourAgent:
    """Test suite for Your Agent."""

    def setup_method(self):
        """Set up test fixtures (runs before each test)."""
        self.agent = YourAgent()

    def test_something(self):
        """Test a specific feature."""
        # Arrange
        input_data = YourInput(...)
        
        # Act
        result = self.agent.process(input_data)
        
        # Assert
        assert result.some_field == expected_value

    @pytest.mark.parametrize("input_val,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
    ])
    def test_with_parameters(self, input_val, expected):
        """Test with multiple parameter sets."""
        result = self.agent.some_method(input_val)
        assert result == expected
```

### Using Fixtures

Fixtures are defined in `conftest.py` and can be used in any test:

```python
def test_with_fixture(sample_requirements_input):
    """Test using a shared fixture."""
    agent = RequirementsAgent()
    result = agent.process(sample_requirements_input)
    assert result is not None
```

### Mocking External APIs

Use `pytest-mock` to mock external API calls:

```python
def test_with_mock(mocker):
    """Test with mocked external API."""
    # Mock Bing Search
    mock_search = mocker.patch('src.services.bing_search.BingSearchClient.search')
    mock_search.return_value = [{"name": "Test", "url": "http://test.com"}]
    
    # Run test
    agent = YourAgent()
    result = agent.some_method()
    
    # Verify mock was called
    mock_search.assert_called_once()
```

---

## 📈 Test Coverage

### View Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open report in browser (macOS)
open htmlcov/index.html

# For other systems
# Linux: xdg-open htmlcov/index.html
# Windows: start htmlcov/index.html
```

### Coverage Goals

- **Target:** 80% code coverage
- **Priority:** High-value code paths (agent processing, orchestration)
- **Focus:** Business logic over boilerplate

### Check Coverage from Terminal

```bash
# Show coverage summary
pytest --cov=src --cov-report=term

# Show missing lines
pytest --cov=src --cov-report=term-missing
```

---

## 🎯 Test Scenarios

### Requirements Agent Tests

- ✅ Cloud platform detection (Azure, AWS, GCP, Oracle)
- ✅ Industry vertical detection
- ✅ Functional requirements extraction
- ✅ Non-functional requirements extraction
- ✅ Compliance detection (HIPAA, PCI DSS, GDPR)
- ✅ Technical constraints extraction
- ✅ Confidence scoring
- ✅ Ambiguity detection

### Architecture Agent Tests (TODO)

- [ ] Azure service selection
- [ ] AWS service selection
- [ ] GCP service selection
- [ ] Well-Architected Framework analysis
- [ ] Mermaid diagram generation
- [ ] Best practices recommendations

### Cost Agent Tests (TODO)

- [ ] Azure pricing calculation
- [ ] Cost scenario generation (LOW/MEDIUM/HIGH)
- [ ] Cost optimization recommendations
- [ ] Multi-cloud cost comparison

### Documentation Agent Tests (TODO)

- [ ] HLD markdown generation
- [ ] Executive summary creation
- [ ] Diagram embedding
- [ ] Table formatting

### Orchestrator Tests (TODO)

- [ ] End-to-end workflow (Requirements → Documentation)
- [ ] Retry logic
- [ ] Error handling
- [ ] Citation deduplication

---

## 🐛 Debugging Tests

### Run Tests in Debug Mode

```bash
# Show full output (no capture)
pytest -s

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Stop on first failure
pytest -x
```

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'src'`

**Solution:** Run tests from project root or add to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:/Users/robenhai/CoPilot-SE"
pytest
```

**Issue:** Tests are slow

**Solution:** Run only unit tests:
```bash
pytest -m "unit and not slow"
```

**Issue:** Tests fail due to missing API keys

**Solution:** Tests should mock external APIs. Check that mocks are properly configured.

---

## 🔄 Continuous Integration

### GitHub Actions (Future)

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## 📝 Test Checklist

Before committing code, ensure:

- [ ] All tests pass: `pytest`
- [ ] Coverage is above 80%: `pytest --cov=src`
- [ ] No linting errors: `pylint src/`
- [ ] Type hints are valid: `mypy src/`
- [ ] Code is formatted: `black src/`

---

## 🆘 Getting Help

- **Pytest Docs:** https://docs.pytest.org/
- **Coverage Docs:** https://coverage.readthedocs.io/
- **Project Docs:** See `docs/` folder
- **Issues:** Create GitHub issue with test failure details

---

**Last Updated:** November 1, 2025  
**Test Status:** Requirements Agent tests complete (18 tests), others pending
