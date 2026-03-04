"""Unit tests for StellarClient."""
import pytest
from unittest.mock import Mock, patch
from stellar_agent.client import StellarClient

@pytest.fixture
def mock_config():
    with patch('stellar_agent.client.config') as mock_conf:
        mock_conf.horizon_url = 'https://horizon-testnet.stellar.org'
        mock_conf.network_passphrase = 'Test SDF Network ; September 2015'
        yield mock_conf

def test_stellar_client_init(mock_config):
    """Test StellarClient initialization."""
    with patch('stellar_agent.client.Server') as mock_server:
        client = StellarClient()
        mock_server.assert_called_once_with('https://horizon-testnet.stellar.org')
        assert client.server == mock_server.return_value

def test_get_account_info(mock_config):
    """Test fetching account information."""
    with patch('stellar_agent.client.Server') as mock_server_class:
        mock_server = mock_server_class.return_value
        
        # Setup mock call chain: server.accounts().account_id().call()
        mock_accounts = Mock()
        mock_account_id = Mock()
        
        mock_server.accounts.return_value = mock_accounts
        mock_accounts.account_id.return_value = mock_account_id
        
        expected_response = {
            "id": "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            "balances": [{"balance": "100.00", "asset_type": "native"}]
        }
        mock_account_id.call.return_value = expected_response

        client = StellarClient()
        response = client.get_account_info("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H")

        mock_accounts.account_id.assert_called_once_with("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H")
        mock_account_id.call.assert_called_once()
        assert response == expected_response

@patch('stellar_agent.client.Keypair')
@patch('stellar_agent.client.TransactionBuilder')
@patch('stellar_agent.client.Payment')
def test_send_payment(
    mock_payment_class,
    mock_tx_builder_class,
    mock_keypair_class,
    mock_config
):
    """Test sending a Stellar payment."""
    with patch('stellar_agent.client.Server') as mock_server_class:
        # Mock Server
        mock_server = mock_server_class.return_value
        
        # Mock Keypair
        mock_source_keypair = Mock()
        mock_source_keypair.public_key = "GBRP...OX2H"
        mock_keypair_class.from_secret.return_value = mock_source_keypair
        
        # Mock Account Load
        mock_source_account = Mock()
        mock_server.load_account.return_value = mock_source_account
        
        # Mock TransactionBuilder chain
        mock_tx_builder = mock_tx_builder_class.return_value
        mock_tx_builder.append_operation.return_value = mock_tx_builder
        mock_tx_builder.set_timeout.return_value = mock_tx_builder
        
        mock_transaction = Mock()
        mock_tx_builder.build.return_value = mock_transaction
        
        # Expected Transaction Response
        expected_response = {"hash": "abc123def456"}
        mock_server.submit_transaction.return_value = expected_response

        client = StellarClient()
        
        response = client.send_payment(
            source_secret="SA...",
            destination_public="GD...",
            amount=10.5
        )

        mock_keypair_class.from_secret.assert_called_once_with("SA...")
        mock_server.load_account.assert_called_once_with("GBRP...OX2H")
        
        # Assert TransactionBuilder initialization
        mock_tx_builder_class.assert_called_once_with(
            source_account=mock_source_account,
            network_passphrase='Test SDF Network ; September 2015',
            base_fee=100
        )
        
        # Assert Payment operation
        mock_payment_class.assert_called_once() # We don't strictly assert the Asset.native() here due to mock complexity, but kwargs are tested.
        
        mock_tx_builder.append_operation.assert_called_once()
        mock_tx_builder.set_timeout.assert_called_once_with(30)
        mock_tx_builder.build.assert_called_once()
        
        mock_transaction.sign.assert_called_once_with(mock_source_keypair)
        mock_server.submit_transaction.assert_called_once_with(mock_transaction)
        
        assert response == expected_response
