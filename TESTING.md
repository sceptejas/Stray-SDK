# Testing Guide

Comprehensive testing guide for Stray SDK.

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_cli.py -v
pytest tests/test_client.py -v
pytest tests/test_config.py -v
pytest tests/test_validators.py -v
```

### Run with Coverage
```bash
pip install pytest-cov
pytest tests/ --cov=stellar_agent --cov-report=term-missing
```

## Test Structure
```
tests/
├── __init__.py
├── test_cli.py          # CLI interface tests (6 tests)
├── test_client.py       # Stellar client tests (6 tests)
├── test_config.py       # Configuration tests (5 tests)
└── test_validators.py   # Validation tests (6 tests)

Total: 23 comprehensive tests
```

## Test Coverage

- **CLI (test_cli.py)**: User input, validation, error handling
- **Client (test_client.py)**: Stellar API interaction, payment flow
- **Config (test_config.py)**: Environment variables, validation
- **Validators (test_validators.py)**: Address and amount validation

## Writing New Tests

### Example Test
```python
import pytest
from stellar_agent.client import StellarClient

def test_example():
    """Test description."""
    result = some_function()
    assert result == expected_value
```

### Using Mocks
```python
from unittest.mock import patch

@patch('stellar_agent.client.Server')
def test_with_mock(mock_server):
    """Test using mocks."""
    client = StellarClient()
    assert client.server is not None
```

## CI/CD

Tests run automatically via GitHub Actions on:
- Every push to master/main/develop
- Every pull request
- Multiple Python versions (3.8-3.12)

Check `.github/workflows/ci.yml` for configuration.

## Code Quality

### Linting
```bash
pip install pylint black
black stellar_agent/ tests/
pylint stellar_agent/
```

### Format Code
```bash
black stellar_agent/
```
