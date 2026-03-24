"""Tests for validation utilities, client balance checks, and configuration."""

from decimal import Decimal
from unittest.mock import patch

import pytest
from stellar_sdk import Keypair

from stellar_agent.client import StellarClient
from stellar_agent.config import config
from stellar_agent.utils.validators import is_valid_amount, is_valid_stellar_address


class TestValidators:
    """Test validation functions."""

    def test_valid_stellar_address(self):
        valid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(valid_address) is True

    def test_invalid_stellar_address_wrong_prefix(self):
        invalid_address = "ABRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(invalid_address) is False

    def test_invalid_stellar_address_wrong_length(self):
        invalid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX"
        assert is_valid_stellar_address(invalid_address) is False

    def test_empty_address(self):
        assert is_valid_stellar_address("") is False

    def test_valid_amount(self):
        assert is_valid_amount(10.5) is True
        assert is_valid_amount(0.0000001) is True

    def test_invalid_amount(self):
        assert is_valid_amount(0) is False
        assert is_valid_amount(-10) is False


class TestStellarClientBalanceChecking:
    """Test balance checking functionality in StellarClient."""

    def setup_method(self):
        self.client = StellarClient()
        self.test_account_id = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"

    @patch.object(StellarClient, "get_account_info")
    def test_get_account_balance_success(self, mock_get_account_info):
        mock_get_account_info.return_value = {
            "balances": [{"asset_type": "native", "balance": "100.5000000"}]
        }

        balance, exists = self.client.get_account_balance(self.test_account_id)
        assert balance == Decimal("100.5000000")
        assert exists is True

    @patch.object(StellarClient, "get_account_info")
    def test_get_account_balance_account_not_found(self, mock_get_account_info):
        mock_get_account_info.side_effect = RuntimeError("Account not found")

        balance, exists = self.client.get_account_balance(self.test_account_id)
        assert balance == Decimal("0")
        assert exists is False

    @patch.object(StellarClient, "get_account_balance")
    def test_check_sufficient_balance_success(self, mock_get_balance):
        mock_get_balance.return_value = (Decimal("100.0"), True)

        sufficient, balance, error_msg = self.client.check_sufficient_balance(
            self.test_account_id, 10.0
        )
        assert sufficient is True
        assert balance == Decimal("100.0")
        assert error_msg == ""

    @patch.object(StellarClient, "get_account_balance")
    def test_check_insufficient_balance(self, mock_get_balance):
        mock_get_balance.return_value = (Decimal("0.5"), True)

        sufficient, balance, error_msg = self.client.check_sufficient_balance(
            self.test_account_id, 10.0
        )
        assert sufficient is False
        assert balance == Decimal("0.5")
        assert "Insufficient balance" in error_msg
        assert "Required:" in error_msg
        assert "Available:" in error_msg

    @patch.object(StellarClient, "get_account_balance")
    def test_check_balance_account_not_found(self, mock_get_balance):
        mock_get_balance.return_value = (Decimal("0"), False)

        sufficient, balance, error_msg = self.client.check_sufficient_balance(
            self.test_account_id, 10.0
        )
        assert sufficient is False
        assert balance == Decimal("0")
        assert error_msg == "Source account not found or not funded"


class TestConfig:
    """Test configuration loading and validation."""

    def test_config_defaults_to_testnet(self):
        with patch.dict("os.environ", {}, clear=True):
            test_config = config.__class__()
            assert test_config.stellar_network == "testnet"
            assert test_config.horizon_url == "https://horizon-testnet.stellar.org"
            assert (
                test_config.network_passphrase
                == "Test SDF Network ; September 2015"
            )
            assert test_config.minimum_balance_xlm == Decimal("1.0")
            assert test_config.balance_check_enabled is True

    def test_config_uses_mainnet_profile(self):
        with patch.dict("os.environ", {"STELLAR_NETWORK": "mainnet"}, clear=True):
            test_config = config.__class__()
            assert test_config.stellar_network == "mainnet"
            assert test_config.horizon_url == "https://horizon.stellar.org"
            assert (
                test_config.network_passphrase
                == "Public Global Stellar Network ; September 2015"
            )

    def test_config_allows_explicit_network_overrides(self):
        with patch.dict(
            "os.environ",
            {
                "STELLAR_NETWORK": "mainnet",
                "HORIZON_URL": "https://custom.example/horizon",
                "NETWORK_PASSPHRASE": "Custom Network",
            },
            clear=True,
        ):
            test_config = config.__class__()
            assert test_config.horizon_url == "https://custom.example/horizon"
            assert test_config.network_passphrase == "Custom Network"

    def test_config_rejects_invalid_boolean_values(self):
        with patch.dict(
            "os.environ",
            {"BALANCE_CHECK_ENABLED": "sometimes"},
            clear=True,
        ):
            with pytest.raises(ValueError, match="BALANCE_CHECK_ENABLED"):
                config.__class__()

    def test_config_validation_missing_source_secret(self):
        with patch.dict("os.environ", {"SOURCE_SECRET": ""}, clear=True):
            test_config = config.__class__()
            with pytest.raises(ValueError, match="SOURCE_SECRET is required"):
                test_config.validate()

    def test_config_validation_invalid_source_secret(self):
        with patch.dict("os.environ", {"SOURCE_SECRET": "invalid_secret"}, clear=True):
            test_config = config.__class__()
            with pytest.raises(
                ValueError, match="SOURCE_SECRET must be a valid Stellar secret seed"
            ):
                test_config.validate()

    def test_config_validation_invalid_optional_account(self):
        source_secret = Keypair.random().secret
        with patch.dict(
            "os.environ",
            {
                "SOURCE_SECRET": source_secret,
                "MONITOR_ACCOUNT_ID": "not-a-public-key",
            },
            clear=True,
        ):
            test_config = config.__class__()
            with pytest.raises(
                ValueError, match="MONITOR_ACCOUNT_ID must be a valid Stellar public key"
            ):
                test_config.validate()

    def test_config_validation_negative_minimum_balance(self):
        source_secret = Keypair.random().secret
        with patch.dict(
            "os.environ",
            {
                "SOURCE_SECRET": source_secret,
                "MINIMUM_BALANCE_XLM": "-0.5",
            },
            clear=True,
        ):
            test_config = config.__class__()
            with pytest.raises(
                ValueError, match="MINIMUM_BALANCE_XLM cannot be negative"
            ):
                test_config.validate()

    def test_config_validation_success(self):
        source_keypair = Keypair.random()
        destination_keypair = Keypair.random()

        with patch.dict(
            "os.environ",
            {
                "SOURCE_SECRET": source_keypair.secret,
                "MONITOR_ACCOUNT_ID": destination_keypair.public_key,
                "DESTINATION_ACCOUNT_ID": destination_keypair.public_key,
                "HORIZON_URL": "https://horizon-testnet.stellar.org",
                "NETWORK_PASSPHRASE": "Test SDF Network ; September 2015",
                "MINIMUM_BALANCE_XLM": "2.5",
                "BALANCE_CHECK_ENABLED": "yes",
            },
            clear=True,
        ):
            test_config = config.__class__()
            assert test_config.validate() is True
            assert test_config.minimum_balance_xlm == Decimal("2.5")
            assert test_config.balance_check_enabled is True
            assert test_config.get_source_public_key() == source_keypair.public_key
