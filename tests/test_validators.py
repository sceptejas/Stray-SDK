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
    
    def test_empty_address(self):
        """Test empty address."""
        assert is_valid_stellar_address("") is False
    
    def test_valid_amount(self):
        """Test valid payment amount."""
        assert is_valid_amount(10.5) is True
        assert is_valid_amount(0.0000001) is True
    
    def test_invalid_amount(self):
        """Test invalid payment amounts."""
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
    
    @staticmethod
    def _account_info(balance, selling_liabilities='0', subentry_count=0):
        """Build a minimal Horizon account payload for mocking."""
        return {
            'subentry_count': subentry_count,
            'balances': [{
                'asset_type': 'native',
                'balance': str(balance),
                'selling_liabilities': str(selling_liabilities),
                'buying_liabilities': '0',
            }],
        }

    @patch.object(StellarClient, 'get_account_info')
    def test_check_sufficient_balance_success(self, mock_info):
        """Account with plenty of XLM, no liabilities, no sub-entries -> OK."""
        mock_info.return_value = self._account_info(balance='100.0')

        sufficient, balance, error_msg = self.client.check_sufficient_balance(
            self.test_account_id, 10.0
        )
        assert sufficient is True
        assert balance == Decimal('100.0')
        assert error_msg == ""

    @patch.object(StellarClient, 'get_account_info')
    def test_check_insufficient_balance(self, mock_info):
        """Tiny total balance cannot cover payment + fee + reserve."""
        mock_info.return_value = self._account_info(balance='0.5')

        sufficient, balance, error_msg = self.client.check_sufficient_balance(
            self.test_account_id, 10.0
        )
        assert sufficient is False
        assert balance == Decimal('0.5')
        assert "Insufficient spendable balance" in error_msg
        assert "Total: 0.5 XLM" in error_msg

    @patch.object(StellarClient, 'get_account_info')
    def test_check_balance_account_not_found(self, mock_info):
        """Non-existent account surfaces a clear error."""
        mock_info.side_effect = RuntimeError("Account not found")

        sufficient, balance, error_msg = self.client.check_sufficient_balance(
            self.test_account_id, 10.0
        )
        assert sufficient is False
        assert balance == Decimal('0')
        assert error_msg == "Source account not found or not funded"

    @patch.object(StellarClient, 'get_account_info')
    def test_selling_liabilities_reduce_spendable_balance(self, mock_info):
        """Regression: XLM locked in open sell offers must not be spendable.

        Before the fix, a 100 XLM account with 95 XLM locked in a sell offer
        was reported as able to send 50 XLM — which the network then rejects.
        """
        mock_info.return_value = self._account_info(
            balance='100.0',
            selling_liabilities='95.0',
        )

        # 50 XLM payment: total balance alone (100) would cover it, but only
        # 4 XLM is actually spendable (100 - 95 - 1 reserve).
        sufficient, total, error_msg = self.client.check_sufficient_balance(
            self.test_account_id, 50.0
        )
        assert sufficient is False
        assert total == Decimal('100.0')
        assert "Selling liabilities: 95.0" in error_msg
        assert "Spendable: 4.0 XLM" in error_msg

    @patch.object(StellarClient, 'get_account_info')
    def test_minimum_reserve_scales_with_subentries(self, mock_info):
        """Regression: minimum reserve depends on subentry_count, not a constant.

        An account with 10 trustlines has a protocol reserve of
        (2 + 10) * 0.5 = 6 XLM. A 4.5 XLM payment fits under a naive
        1 XLM reserve assumption but exceeds the real reserve.
        """
        mock_info.return_value = self._account_info(
            balance='10.0',
            subentry_count=10,
        )

        # Total 10, reserve 6, fee 0.00001 -> spendable ~3.99999 XLM.
        sufficient, total, error_msg = self.client.check_sufficient_balance(
            self.test_account_id, 4.5
        )
        assert sufficient is False
        assert total == Decimal('10.0')
        assert "Reserve: 6.0" in error_msg

    @patch.object(StellarClient, 'get_account_info')
    def test_reserve_uses_zero_subentries_for_fresh_account(self, mock_info):
        """A fresh account (0 sub-entries) reserves exactly 1 XLM (2 * 0.5)."""
        mock_info.return_value = self._account_info(
            balance='5.0',
            subentry_count=0,
        )

        # 3.9 XLM payment -> spendable = 5 - 0 - 1 = 4, fee 0.00001 -> OK.
        sufficient, _, error_msg = self.client.check_sufficient_balance(
            self.test_account_id, 3.9
        )
        assert sufficient is True, error_msg

    @patch.object(StellarClient, 'get_account_info')
    def test_reserve_fallback_when_subentry_count_missing(self, mock_info):
        """If Horizon omits subentry_count, fall back to config.minimum_balance_xlm."""
        # Payload without subentry_count.
        mock_info.return_value = {
            'balances': [{
                'asset_type': 'native',
                'balance': '100.0',
                'selling_liabilities': '0',
            }],
        }

        sufficient, balance, _ = self.client.check_sufficient_balance(
            self.test_account_id, 10.0
        )
        assert sufficient is True
        assert balance == Decimal('100.0')

    @patch.object(StellarClient, 'get_account_info')
    def test_get_spendable_balance_subtracts_liabilities_and_reserve(self, mock_info):
        """The new helper returns exactly balance - selling - reserve."""
        mock_info.return_value = self._account_info(
            balance='50.0',
            selling_liabilities='5.0',
            subentry_count=4,  # reserve = (2+4)*0.5 = 3
        )

        spendable, exists = self.client.get_spendable_balance(self.test_account_id)
        assert exists is True
        assert spendable == Decimal('42.0')  # 50 - 5 - 3


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
