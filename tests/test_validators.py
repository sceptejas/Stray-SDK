"""Tests for validation utilities and client balance checks."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from stellar_agent.utils.validators import is_valid_stellar_address, is_valid_amount
from stellar_agent.client import StellarClient
from stellar_agent.config import config
from stellar_sdk.exceptions import NotFoundError, BadRequestError

class TestValidators:
    """Test validation functions."""
    
    def test_valid_stellar_address(self):
        """Test valid Stellar address format."""
        valid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(valid_address) is True
    
    def test_invalid_stellar_address_wrong_prefix(self):
        """Test address with wrong prefix."""
        invalid_address = "ABRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(invalid_address) is False
    
    def test_invalid_stellar_address_wrong_length(self):
        """Test address with wrong length."""
        invalid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX"
        assert is_valid_stellar_address(invalid_address) is False
    
    def test_invalid_stellar_address_invalid_characters(self):
        """Test address with invalid characters."""
        invalid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2I"
        assert is_valid_stellar_address(invalid_address) is False
    
    def test_empty_address(self):
        """Test empty address."""
        assert is_valid_stellar_address("") is False
    
    def test_none_address(self):
        """Test None address."""
        assert is_valid_stellar_address(None) is False
    
    def test_whitespace_address(self):
        """Test address with whitespace."""
        assert is_valid_stellar_address("  ") is False
        assert is_valid_stellar_address(" GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H ") is False
    
    def test_valid_amount(self):
        """Test valid payment amount."""
        assert is_valid_amount(10.5) is True
        assert is_valid_amount(0.0000001) is True
        assert is_valid_amount(1.0) is True
        assert is_valid_amount(1000000.0) is True
    
    def test_invalid_amount(self):
        """Test invalid payment amounts."""
        assert is_valid_amount(0) is False
        assert is_valid_amount(-10) is False
        assert is_valid_amount(-0.0001) is False
    
    def test_amount_edge_cases(self):
        """Test edge cases for amount validation."""
        # Very small positive amounts
        assert is_valid_amount(0.0000001) is True
        # Zero amount
        assert is_valid_amount(0.0) is False
        # Negative amounts
        assert is_valid_amount(-0.0000001) is False


class TestStellarClientBalanceChecking:
    """Test balance checking functionality in StellarClient."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = StellarClient()
        self.test_account_id = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
    
    @patch.object(StellarClient, 'get_account_info')
    def test_get_account_balance_success(self, mock_get_account_info):
        """Test successful balance retrieval."""
        mock_get_account_info.return_value = {
            'balances': [
                {'asset_type': 'native', 'balance': '100.5000000'}
            ]
        }
        
        balance, exists = self.client.get_account_balance(self.test_account_id)
        assert balance == Decimal('100.5000000')
        assert exists is True
    
    @patch.object(StellarClient, 'get_account_info')
    def test_get_account_balance_multiple_assets(self, mock_get_account_info):
        """Test balance retrieval with multiple assets."""
        mock_get_account_info.return_value = {
            'balances': [
                {'asset_type': 'credit_alphanum4', 'asset_code': 'USD', 'balance': '50.0000000'},
                {'asset_type': 'native', 'balance': '25.7500000'},
                {'asset_type': 'credit_alphanum12', 'asset_code': 'EUR', 'balance': '100.0000000'}
            ]
        }
        
        balance, exists = self.client.get_account_balance(self.test_account_id)
        assert balance == Decimal('25.7500000')
        assert exists is True
    
    @patch.object(StellarClient, 'get_account_info')
    def test_get_account_balance_no_native_asset(self, mock_get_account_info):
        """Test balance retrieval when account has no XLM."""
        mock_get_account_info.return_value = {
            'balances': [
                {'asset_type': 'credit_alphanum4', 'asset_code': 'USD', 'balance': '50.0000000'}
            ]
        }
        
        balance, exists = self.client.get_account_balance(self.test_account_id)
        assert balance == Decimal('0')
        assert exists is True
    
    @patch.object(StellarClient, 'get_account_info')
    def test_get_account_balance_empty_balances(self, mock_get_account_info):
        """Test balance retrieval with empty balances array."""
        mock_get_account_info.return_value = {
            'balances': []
        }
        
        balance, exists = self.client.get_account_balance(self.test_account_id)
        assert balance == Decimal('0')
        assert exists is True
    
    @patch.object(StellarClient, 'get_account_info')
    def test_get_account_balance_account_not_found(self, mock_get_account_info):
        """Test balance check for non-existent account."""
        mock_get_account_info.side_effect = RuntimeError("Account not found")
        
        balance, exists = self.client.get_account_balance(self.test_account_id)
        assert balance == Decimal('0')
        assert exists is False
    
    @patch.object(StellarClient, 'get_account_balance')
    def test_check_sufficient_balance_success(self, mock_get_balance):
        """Test sufficient balance check."""
        mock_get_balance.return_value = (Decimal('100.0'), True)
        
        sufficient, balance, error_msg = self.client.check_sufficient_balance(self.test_account_id, 10.0)
        assert sufficient is True
        assert balance == Decimal('100.0')
        assert error_msg == ""
    
    @patch.object(StellarClient, 'get_account_balance')
    def test_check_insufficient_balance(self, mock_get_balance):
        """Test insufficient balance check."""
        mock_get_balance.return_value = (Decimal('0.5'), True)
        
        sufficient, balance, error_msg = self.client.check_sufficient_balance(self.test_account_id, 10.0)
        assert sufficient is False
        assert balance == Decimal('0.5')
        assert "Insufficient balance" in error_msg
        assert "Required:" in error_msg
        assert "Available:" in error_msg
    
    @patch.object(StellarClient, 'get_account_balance')
    def test_check_balance_exact_minimum(self, mock_get_balance):
        """Test balance check with exact minimum required."""
        # Set balance to exactly minimum reserve + fee + payment
        payment_amount = 10.0
        estimated_fee = Decimal('0.00001')
        minimum_reserve = Decimal('1.0')
        total_required = payment_amount + estimated_fee + minimum_reserve
        
        mock_get_balance.return_value = (total_required, True)
        
        sufficient, balance, error_msg = self.client.check_sufficient_balance(self.test_account_id, payment_amount)
        assert sufficient is True
        assert balance == total_required
        assert error_msg == ""
    
    @patch.object(StellarClient, 'get_account_balance')
    def test_check_balance_just_under_minimum(self, mock_get_balance):
        """Test balance check just under minimum required."""
        payment_amount = 10.0
        estimated_fee = Decimal('0.00001')
        minimum_reserve = Decimal('1.0')
        total_required = payment_amount + estimated_fee + minimum_reserve
        
        # Set balance just under required
        mock_get_balance.return_value = (total_required - Decimal('0.00001'), True)
        
        sufficient, balance, error_msg = self.client.check_sufficient_balance(self.test_account_id, payment_amount)
        assert sufficient is False
        assert balance == total_required - Decimal('0.00001')
        assert "Insufficient balance" in error_msg
    
    @patch.object(StellarClient, 'get_account_balance')
    def test_check_balance_account_not_found(self, mock_get_balance):
        """Test balance check for account that doesn't exist."""
        mock_get_balance.return_value = (Decimal('0'), False)
        
        sufficient, balance, error_msg = self.client.check_sufficient_balance(self.test_account_id, 10.0)
        assert sufficient is False
        assert balance == Decimal('0')
        assert error_msg == "Source account not found or not funded"


class TestStellarClientPaymentFlow:
    """Test payment flow functionality in StellarClient."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = StellarClient()
        self.test_source_secret = "SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        self.test_destination = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        self.test_amount = 10.5
    
    @patch('stellar_agent.client.Keypair')
    @patch('stellar_agent.client.TransactionBuilder')
    @patch('stellar_agent.client.Payment')
    @patch('stellar_agent.client.Asset')
    def test_send_payment_success(self, mock_asset, mock_payment_class, mock_tx_builder_class, mock_keypair_class):
        """Test successful payment sending."""
        # Mock Keypair
        mock_source_keypair = Mock()
        mock_source_keypair.public_key = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        mock_keypair_class.from_secret.return_value = mock_source_keypair
        
        # Mock server operations
        with patch.object(self.client, 'server') as mock_server:
            # Mock account loading
            mock_source_account = Mock()
            mock_server.load_account.return_value = mock_source_account
            
            # Mock transaction building
            mock_tx_builder = Mock()
            mock_tx_builder.append_operation.return_value = mock_tx_builder
            mock_tx_builder.set_timeout.return_value = mock_tx_builder
            mock_tx_builder.build.return_value = Mock()
            mock_tx_builder_class.return_value = mock_tx_builder
            
            # Mock transaction submission
            expected_response = {"hash": "abc123def456", "successful": True}
            mock_server.submit_transaction.return_value = expected_response
            
            # Mock Asset.native()
            mock_asset.native.return_value = "native_asset"
            
            # Execute payment
            response = self.client.send_payment(self.test_source_secret, self.test_destination, self.test_amount)
            
            # Assertions
            mock_keypair_class.from_secret.assert_called_once_with(self.test_source_secret)
            mock_server.load_account.assert_called_once_with(mock_source_keypair.public_key)
            mock_server.submit_transaction.assert_called_once()
            assert response == expected_response
    
    @patch('stellar_agent.client.Keypair')
    def test_send_payment_invalid_secret(self, mock_keypair_class):
        """Test payment with invalid secret key."""
        mock_keypair_class.from_secret.side_effect = Exception("Invalid secret")
        
        with pytest.raises(RuntimeError, match="Payment operation failed"):
            self.client.send_payment(self.test_source_secret, self.test_destination, self.test_amount)
    
    @patch('stellar_agent.client.Keypair')
    @patch.object(StellarClient, 'check_sufficient_balance')
    def test_send_payment_insufficient_balance(self, mock_check_balance, mock_keypair_class):
        """Test payment with insufficient balance."""
        # Mock Keypair
        mock_source_keypair = Mock()
        mock_source_keypair.public_key = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        mock_keypair_class.from_secret.return_value = mock_source_keypair
        
        # Mock balance check to fail
        mock_check_balance.return_value = (False, Decimal('0.5'), "Insufficient balance")
        
        with patch.object(config, 'balance_check_enabled', True):
            with pytest.raises(RuntimeError, match="Balance check failed"):
                self.client.send_payment(self.test_source_secret, self.test_destination, self.test_amount)
    
    @patch('stellar_agent.client.Keypair')
    def test_send_payment_source_account_not_found(self, mock_keypair_class):
        """Test payment when source account doesn't exist."""
        # Mock Keypair
        mock_source_keypair = Mock()
        mock_source_keypair.public_key = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        mock_keypair_class.from_secret.return_value = mock_source_keypair
        
        # Mock server to raise NotFoundError
        with patch.object(self.client, 'server') as mock_server:
            mock_server.load_account.side_effect = NotFoundError("Account not found")
            
            with pytest.raises(RuntimeError, match="Source account .* not found"):
                self.client.send_payment(self.test_source_secret, self.test_destination, self.test_amount)


class TestConfig:
    """Test configuration validation."""
    
    def test_config_validation_missing_source_secret(self):
        """Test config validation fails with missing SOURCE_SECRET."""
        with patch.dict('os.environ', {'SOURCE_SECRET': ''}, clear=True):
            test_config = config.__class__()
            with pytest.raises(ValueError, match="SOURCE_SECRET is required"):
                test_config.validate()
    
    def test_config_validation_invalid_source_secret(self):
        """Test config validation fails with invalid SOURCE_SECRET format."""
        with patch.dict('os.environ', {'SOURCE_SECRET': 'invalid_secret'}, clear=True):
            test_config = config.__class__()
            with pytest.raises(ValueError, match="SOURCE_SECRET must be a valid Stellar secret key"):
                test_config.validate()
    
    @patch.dict('os.environ', {
        'SOURCE_SECRET': 'SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
        'HORIZON_URL': 'https://horizon-testnet.stellar.org',
        'NETWORK_PASSPHRASE': 'Test SDF Network ; September 2015'
    })
    def test_config_validation_success(self):
        """Test config validation succeeds with valid values."""
        test_config = config.__class__()
        assert test_config.validate() is True
