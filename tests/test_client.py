"""Unit tests for StellarClient."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from stellar_agent.client import StellarClient
from stellar_sdk.exceptions import NotFoundError, BadRequestError
from decimal import Decimal

@pytest.fixture
def mock_config():
    with patch('stellar_agent.client.config') as mock_conf:
        mock_conf.horizon_url = 'https://horizon-testnet.stellar.org'
        mock_conf.network_passphrase = 'Test SDF Network ; September 2015'
        mock_conf.minimum_balance_xlm = 1.0
        mock_conf.balance_check_enabled = True
        yield mock_conf

def test_stellar_client_init(mock_config):
    """Test StellarClient initialization."""
    with patch('stellar_agent.client.Server') as mock_server:
        client = StellarClient()
        mock_server.assert_called_once_with('https://horizon-testnet.stellar.org')
        assert client.server == mock_server.return_value

def test_stellar_client_init_custom_config():
    """Test StellarClient initialization with custom config."""
    with patch('stellar_agent.client.config') as mock_conf:
        mock_conf.horizon_url = 'https://custom-horizon.stellar.org'
        mock_conf.network_passphrase = 'Custom Network'
        mock_conf.minimum_balance_xlm = 2.0
        mock_conf.balance_check_enabled = False
        
        with patch('stellar_agent.client.Server') as mock_server:
            client = StellarClient()
            mock_server.assert_called_once_with('https://custom-horizon.stellar.org')
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
            "balances": [{"balance": "100.00", "asset_type": "native"}],
            "sequence": 123456789
        }
        mock_account_id.call.return_value = expected_response

        client = StellarClient()
        response = client.get_account_info("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H")

        mock_accounts.account_id.assert_called_once_with("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H")
        mock_account_id.call.assert_called_once()
        assert response == expected_response

def test_get_account_info_not_found_error(mock_config):
    """Test fetching account info for non-existent account."""
    with patch('stellar_agent.client.Server') as mock_server_class:
        mock_server = mock_server_class.return_value
        mock_accounts = Mock()
        mock_account_id = Mock()
        
        mock_server.accounts.return_value = mock_accounts
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.side_effect = NotFoundError("Account not found")
        
        client = StellarClient()
        
        with pytest.raises(RuntimeError, match="Account GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H not found"):
            client.get_account_info("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H")

def test_get_account_info_network_error(mock_config):
    """Test fetching account info with network error."""
    with patch('stellar_agent.client.Server') as mock_server_class:
        mock_server = mock_server_class.return_value
        mock_accounts = Mock()
        mock_account_id = Mock()
        
        mock_server.accounts.return_value = mock_accounts
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.side_effect = Exception("Network timeout")
        
        client = StellarClient()
        
        with pytest.raises(RuntimeError, match="Failed to fetch account information"):
            client.get_account_info("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H")

@patch('stellar_agent.client.Keypair')
@patch('stellar_agent.client.TransactionBuilder')
@patch('stellar_agent.client.Payment')
@patch('stellar_agent.client.Asset')
def test_send_payment(
    mock_asset,
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
        expected_response = {"hash": "abc123def456", "successful": True}
        mock_server.submit_transaction.return_value = expected_response
        
        # Mock Asset.native()
        mock_asset.native.return_value = "native_asset"

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
        mock_payment_class.assert_called_once()
        
        mock_tx_builder.append_operation.assert_called_once()
        mock_tx_builder.set_timeout.assert_called_once_with(30)
        mock_tx_builder.build.assert_called_once()
        
        mock_transaction.sign.assert_called_once_with(mock_source_keypair)
        mock_server.submit_transaction.assert_called_once_with(mock_transaction)
        
        assert response == expected_response

@patch('stellar_agent.client.Keypair')
def test_send_payment_invalid_secret_key(mock_keypair_class, mock_config):
    """Test sending payment with invalid secret key."""
    mock_keypair_class.from_secret.side_effect = Exception("Invalid secret key format")
    
    with patch('stellar_agent.client.Server') as mock_server_class:
        client = StellarClient()
        
        with pytest.raises(RuntimeError, match="Payment operation failed"):
            client.send_payment(
                source_secret="invalid_secret",
                destination_public="GD...",
                amount=10.5
            )

@patch('stellar_agent.client.Keypair')
def test_send_payment_balance_check_enabled_insufficient(mock_keypair_class, mock_config):
    """Test payment with balance check enabled and insufficient balance."""
    # Mock Keypair
    mock_source_keypair = Mock()
    mock_source_keypair.public_key = "GBRP...OX2H"
    mock_keypair_class.from_secret.return_value = mock_source_keypair
    
    with patch('stellar_agent.client.Server') as mock_server_class:
        client = StellarClient()
        
        # Mock balance check to fail
        with patch.object(client, 'check_sufficient_balance') as mock_check_balance:
            mock_check_balance.return_value = (False, Decimal('0.5'), "Insufficient balance")
            
            with pytest.raises(RuntimeError, match="Balance check failed"):
                client.send_payment(
                    source_secret="SA...",
                    destination_public="GD...",
                    amount=10.5
                )

@patch('stellar_agent.client.Keypair')
def test_send_payment_source_account_not_found(mock_keypair_class, mock_config):
    """Test payment when source account doesn't exist."""
    # Mock Keypair
    mock_source_keypair = Mock()
    mock_source_keypair.public_key = "GBRP...OX2H"
    mock_keypair_class.from_secret.return_value = mock_source_keypair
    
    with patch('stellar_agent.client.Server') as mock_server_class:
        mock_server = mock_server_class.return_value
        mock_server.load_account.side_effect = NotFoundError("Account not found")
        
        client = StellarClient()
        
        with pytest.raises(RuntimeError, match="Source account .* not found"):
            client.send_payment(
                source_secret="SA...",
                destination_public="GD...",
                amount=10.5
            )

@patch('stellar_agent.client.Keypair')
@patch('stellar_agent.client.TransactionBuilder')
@patch('stellar_agent.client.Payment')
@patch('stellar_agent.client.Asset')
def test_send_payment_bad_request_insufficient_balance(
    mock_asset,
    mock_payment_class,
    mock_tx_builder_class,
    mock_keypair_class,
    mock_config
):
    """Test payment with insufficient balance at transaction submission."""
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
        mock_tx_builder.build.return_value = Mock()
        
        # Mock transaction submission to fail with insufficient balance
        mock_server.submit_transaction.side_effect = BadRequestError("insufficient balance")
        
        # Mock Asset.native()
        mock_asset.native.return_value = "native_asset"
        
        client = StellarClient()
        
        with pytest.raises(RuntimeError, match="Transaction failed: Insufficient balance"):
            client.send_payment(
                source_secret="SA...",
                destination_public="GD...",
                amount=10.5
            )

@patch('stellar_agent.client.Keypair')
@patch('stellar_agent.client.TransactionBuilder')
@patch('stellar_agent.client.Payment')
@patch('stellar_agent.client.Asset')
def test_send_payment_destination_not_exist(
    mock_asset,
    mock_payment_class,
    mock_tx_builder_class,
    mock_keypair_class,
    mock_config
):
    """Test payment to non-existent destination account."""
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
        mock_tx_builder.build.return_value = Mock()
        
        # Mock transaction submission to fail with destination not exist
        mock_server.submit_transaction.side_effect = BadRequestError("destination account does not exist")
        
        # Mock Asset.native()
        mock_asset.native.return_value = "native_asset"
        
        client = StellarClient()
        
        with pytest.raises(RuntimeError, match="Transaction failed: Destination account does not exist"):
            client.send_payment(
                source_secret="SA...",
                destination_public="GD...",
                amount=10.5
            )
