"""Tests for validation utilities and client balance checks."""
import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from stellar_agent.utils.validators import is_valid_stellar_address, is_valid_amount
from stellar_agent.client import StellarClient
from stellar_agent.config import config

class TestValidators:
    """Test validation functions."""
    
    def test_valid_stellar_address(self):
        """Test valid Stellar address format with cryptographic validation."""
        # Known valid Stellar public key
        valid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(valid_address) is True
        
        # Another known valid address
        valid_address2 = "GA7QYNF7SOWQ3GLR2BGMZEHXAVIRZA4KVWLTJJFC7MGXUA74P7UJVSGZ"
        assert is_valid_stellar_address(valid_address2) is True
    
    def test_invalid_stellar_address_wrong_prefix(self):
        """Test address with wrong prefix."""
        invalid_address = "ABRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(invalid_address) is False
        
        # Test with other invalid prefixes
        invalid_address2 = "SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H" # S is for secret keys
        assert is_valid_stellar_address(invalid_address2) is False
    
    def test_invalid_stellar_address_wrong_length(self):
        """Test address with wrong length."""
        # Too short
        invalid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX"
        assert is_valid_stellar_address(invalid_address) is False
        
        # Too long
        invalid_address2 = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2HZ"
        assert is_valid_stellar_address(invalid_address2) is False
    
    def test_invalid_stellar_address_bad_characters(self):
        """Test address with invalid characters."""
        # Contains invalid characters (0, 1, 8, 9 not in Base32)
        invalid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX01"
        assert is_valid_stellar_address(invalid_address) is False
        
        # Contains lowercase (should be uppercase)
        invalid_address2 = "gbrpyhil2ci3fnq4bxlfmndlfjunpu2hy3zmfshonuceoasw7qc7ox2h"
        assert is_valid_stellar_address(invalid_address2) is False
    
    def test_invalid_stellar_address_bad_checksum(self):
        """Test address with valid format but invalid checksum (fails crypto validation)."""
        # This has correct format but invalid checksum
        invalid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2Z"
        assert is_valid_stellar_address(invalid_address) is False
    
    def test_empty_address(self):
        """Test empty and None address."""
        assert is_valid_stellar_address("") is False
        assert is_valid_stellar_address(None) is False  # Test with None
    
    def test_whitespace_address(self):
        """Test address with whitespace."""
        # Leading/trailing whitespace should not be accepted
        valid_core = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(f" {valid_core}") is False
        assert is_valid_stellar_address(f"{valid_core} ") is False
        assert is_valid_stellar_address(f" {valid_core} ") is False
    
    def test_valid_amount(self):
        """Test valid payment amounts."""
        assert is_valid_amount(10.5) is True
        assert is_valid_amount(0.0000001) is True  # Minimum XLM amount
        assert is_valid_amount(1000000.0) is True  # Large amount
        assert is_valid_amount(1) is True  # Integer amounts
    
    def test_invalid_amount(self):
        """Test invalid payment amounts."""
        assert is_valid_amount(0) is False  # Zero amount
        assert is_valid_amount(-10) is False  # Negative amount
        assert is_valid_amount(-0.001) is False  # Negative small amount
        assert is_valid_amount(0) is False
        assert is_valid_amount(-10) is False


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
    def test_check_balance_account_not_found(self, mock_get_balance):
        """Test balance check for account that doesn't exist."""
        mock_get_balance.return_value = (Decimal('0'), False)
        
        sufficient, balance, error_msg = self.client.check_sufficient_balance(self.test_account_id, 10.0)
        assert sufficient is False
        assert balance == Decimal('0')
        assert error_msg == "Source account not found or not funded"


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
