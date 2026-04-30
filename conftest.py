"""Pytest configuration and shared fixtures."""
import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from stellar_agent.client import StellarClient
from stellar_agent.config import config

@pytest.fixture
def mock_stellar_client():
    """Mock StellarClient instance for testing."""
    with patch('stellar_agent.client.Server') as mock_server:
        client = StellarClient()
        yield client

@pytest.fixture
def sample_account_data():
    """Sample account data for testing."""
    return {
        "id": "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
        "account_id": "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
        "sequence": 123456789,
        "balances": [
            {"asset_type": "native", "balance": "100.5000000"},
            {"asset_type": "credit_alphanum4", "asset_code": "USD", "issuer": "GD...", "balance": "50.0000000"}
        ],
        "flags": {
            "auth_required": False,
            "auth_revocable": False,
            "auth_immutable": False
        },
        "thresholds": {
            "low_threshold": 1,
            "med_threshold": 2,
            "high_threshold": 3
        }
    }

@pytest.fixture
def sample_transaction_response():
    """Sample transaction response for testing."""
    return {
        "hash": "abc123def456789012345678901234567890abcdef1234567890abcdef1234567890",
        "ledger": 12345,
        "envelope_xdr": "AAAAAgAAAAB...",
        "result_xdr": "AAAAAAAAAGQ...",
        "result_meta_xdr": "AAAAAgAAAAE...",
        "fee_charged": 100,
        "fee_meta_xdr": "AAAAAgAAAAA...",
        "memo_type": "none",
        "signatures": [
            {
                "hint": "abc123",
                "key": "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
                "signature": "def456..."
            }
        ],
        "successful": True,
        "created_at": "2023-01-01T00:00:00Z",
        "source_account": "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
    }

@pytest.fixture
def valid_stellar_address():
    """Valid Stellar address for testing."""
    return "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"

@pytest.fixture
def invalid_stellar_addresses():
    """Collection of invalid Stellar addresses for testing."""
    return [
        "ABRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",  # Wrong prefix
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX",    # Too short
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2HH", # Too long
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2I",  # Invalid character
        "",  # Empty
        None,  # None
        "   ",  # Whitespace
        " GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H "  # Leading/trailing whitespace
    ]

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch('stellar_agent.client.config') as mock_conf:
        mock_conf.horizon_url = 'https://horizon-testnet.stellar.org'
        mock_conf.network_passphrase = 'Test SDF Network ; September 2015'
        mock_conf.minimum_balance_xlm = 1.0
        mock_conf.balance_check_enabled = True
        mock_conf.source_secret = 'SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H'
        yield mock_conf

@pytest.fixture
def sample_payment_data():
    """Sample payment data for testing."""
    return {
        "source_secret": "SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
        "destination_public": "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
        "amount": 10.5,
        "asset_type": "native"
    }

# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )

# Helper functions for tests
def create_mock_server_response(response_data):
    """Create a mock server response for testing."""
    mock_server = Mock()
    mock_accounts = Mock()
    mock_account_id = Mock()
    
    mock_server.accounts.return_value = mock_accounts
    mock_accounts.account_id.return_value = mock_account_id
    mock_account_id.call.return_value = response_data
    
    return mock_server

def create_mock_transaction_builder():
    """Create a mock transaction builder for testing."""
    mock_tx_builder = Mock()
    mock_tx_builder.append_operation.return_value = mock_tx_builder
    mock_tx_builder.set_timeout.return_value = mock_tx_builder
    mock_tx_builder.build.return_value = Mock()
    return mock_tx_builder
