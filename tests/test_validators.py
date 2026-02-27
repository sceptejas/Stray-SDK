"""Tests for validation utilities and client functionality."""
import pytest
from unittest.mock import Mock, patch
from stellar_agent.utils.validators import (
    is_valid_stellar_address,
    is_valid_amount,
    format_stellar_amount
)
from stellar_agent.client import StellarClient, PaymentError
from stellar_sdk.exceptions import NotFoundError, BadRequestError


class TestIsValidStellarAddress:
    """Test Stellar address validation using SDK's Ed25519 verification."""

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

    def test_structurally_valid_but_invalid_ed25519(self):
        """
        Regression test for bug #2.
        Regex passes but SDK rejects invalid Ed25519 keys.
        """
        # All 'A's passes regex r'^G[A-Z2-7]{55}$' but fails Ed25519 check
        invalid_key = "G" + "A" * 55
        assert is_valid_stellar_address(invalid_key) is False

    def test_whitespace_address(self):
        """Test address with only whitespace."""
        assert is_valid_stellar_address("   ") is False


class TestIsValidAmount:
    """Test amount validation with Stellar's 7-decimal and minimum stroop rules."""

    def test_valid_positive_amount(self):
        """Test valid positive payment amount."""
        assert is_valid_amount(10.5) is True

    def test_valid_minimum_stroop(self):
        """Test minimum valid amount (1 stroop = 0.0000001 XLM)."""
        assert is_valid_amount(0.0000001) is True

    def test_invalid_zero(self):
        """Test zero amount."""
        assert is_valid_amount(0) is False

    def test_invalid_negative(self):
        """Test negative payment amount."""
        assert is_valid_amount(-10) is False

    def test_invalid_over_7_decimals(self):
        """
        Regression test for bug #5.
        Amounts with >7 decimals should be rejected.
        """
        assert is_valid_amount(0.00000001) is False  # 8 decimals
        assert is_valid_amount(1.123456789) is False  # 9 decimals

    def test_valid_exactly_7_decimals(self):
        """Test amount with exactly 7 decimals is accepted."""
        assert is_valid_amount(1.1234567) is True

    def test_invalid_sub_stroop(self):
        """Test sub-stroop amounts are rejected."""
        assert is_valid_amount(0.00000009) is False


class TestFormatStellarAmount:
    """Test format_stellar_amount helper for Decimal-based formatting."""

    def test_float_arithmetic_artifact_fixed(self):
        """
        Regression test for bug #1.
        str(0.1 + 0.2) produces '0.30000000000000004' which SDK rejects.
        """
        result = format_stellar_amount(0.1 + 0.2)
        assert result == "0.3"

    def test_whole_number_strips_decimals(self):
        """Test whole numbers are formatted without trailing .0"""
        assert format_stellar_amount(10.0) == "10"

    def test_one_third_truncates_to_7_decimals(self):
        """Test repeating decimal is truncated to 7 places."""
        result = format_stellar_amount(1 / 3)
        assert result == "0.3333333"

    def test_minimum_stroop_preserved(self):
        """Test minimum stroop (0.0000001) is formatted correctly."""
        assert format_stellar_amount(0.0000001) == "0.0000001"

    def test_large_integer(self):
        """Test large integer amounts."""
        assert format_stellar_amount(1000000) == "1000000"


class TestStellarClientSendPayment:
    """Test StellarClient.send_payment with mocked Horizon."""

    @patch('stellar_agent.client.Server')
    def test_successful_payment_returns_hash(self, mock_server_class):
        """Test successful payment returns transaction hash."""
        # Mock Horizon responses
        mock_server = Mock()
        mock_server_class.return_value = mock_server

        # Mock account_exists check (returns True)
        mock_account_response = Mock()
        mock_server.accounts().account_id().call.return_value = mock_account_response

        # Mock load_account
        mock_account = Mock()
        mock_account.sequence = 1234567890
        mock_server.load_account.return_value = mock_account

        # Mock successful transaction submission
        mock_server.submit_transaction.return_value = {
            'hash': 'abc123def456',
            'result': 'success'
        }

        client = StellarClient()
        response = client.send_payment(
            "SACFBIKSA5AFZFVJGQFLJXEQ5Z7VM3CAHCHZDA5F4I5GJDXM7TKXQP74",  # Valid testnet secret
            "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            10.0
        )

        assert response['hash'] == 'abc123def456'

    @patch('stellar_agent.client.Server')
    def test_nonexistent_destination_raises_payment_error(self, mock_server_class):
        """
        Regression test for bug #4.
        Pre-flight check should catch non-existent destination.
        """
        mock_server = Mock()
        mock_server_class.return_value = mock_server

        # Mock account_exists returns NotFoundError
        mock_server.accounts().account_id().call.side_effect = NotFoundError(Mock())

        client = StellarClient()

        with pytest.raises(PaymentError) as exc_info:
            client.send_payment(
                "SACFBIKSA5AFZFVJGQFLJXEQ5Z7VM3CAHCHZDA5F4I5GJDXM7TKXQP74",  # Valid testnet secret
                "GDOESNOTEXIST1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ12",
                10.0
            )

        assert "does not exist" in str(exc_info.value)

    @patch('stellar_agent.client.Server')
    def test_overprecise_float_safe(self, mock_server_class):
        """
        Regression test for bug #1.
        format_stellar_amount prevents SDK exception on float artifacts.
        """
        mock_server = Mock()
        mock_server_class.return_value = mock_server

        mock_server.accounts().account_id().call.return_value = Mock()
        mock_account = Mock()
        mock_account.sequence = 1234567890
        mock_server.load_account.return_value = mock_account
        mock_server.submit_transaction.return_value = {'hash': 'test_hash'}

        client = StellarClient()

        # This should NOT raise ValueError from Payment() constructor
        response = client.send_payment(
            "SACFBIKSA5AFZFVJGQFLJXEQ5Z7VM3CAHCHZDA5F4I5GJDXM7TKXQP74",  # Valid testnet secret
            "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            0.1 + 0.2  # Produces '0.30000000000000004' as str(float)
        )

        assert response['hash'] == 'test_hash'

    @patch('stellar_agent.client.Server')
    def test_memo_support(self, mock_server_class):
        """
        Test memo feature (bug #8).
        Memo should be passed to TransactionBuilder.
        """
        mock_server = Mock()
        mock_server_class.return_value = mock_server

        mock_server.accounts().account_id().call.return_value = Mock()
        mock_account = Mock()
        mock_account.sequence = 1234567890
        mock_server.load_account.return_value = mock_account
        mock_server.submit_transaction.return_value = {'hash': 'memo_test_hash'}

        client = StellarClient()

        # Send with memo
        response = client.send_payment(
            "SACFBIKSA5AFZFVJGQFLJXEQ5Z7VM3CAHCHZDA5F4I5GJDXM7TKXQP74",  # Valid testnet secret
            "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            5.0,
            memo="test-memo-12345"
        )

        assert response['hash'] == 'memo_test_hash'


class TestStellarClientAccountExists:
    """Test StellarClient.account_exists pre-flight check."""

    @patch('stellar_agent.client.Server')
    def test_account_exists_returns_true(self, mock_server_class):
        """Test account_exists returns True for existing account."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.accounts().account_id().call.return_value = {'id': 'test_account'}

        client = StellarClient()
        assert client.account_exists("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H") is True

    @patch('stellar_agent.client.Server')
    def test_account_exists_returns_false_on_not_found(self, mock_server_class):
        """Test account_exists returns False when NotFoundError is raised."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.accounts().account_id().call.side_effect = NotFoundError(Mock())

        client = StellarClient()
        assert client.account_exists("GDOESNOTEXIST1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ12") is False


class TestStellarClientGetBalance:
    """Test balance checking functionality (Issue #7)."""

    @patch('stellar_agent.client.Server')
    def test_get_balance_returns_native_xlm(self, mock_server_class):
        """Test get_balance returns native XLM balance."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.accounts().account_id().call.return_value = {
            'balances': [
                {'asset_type': 'native', 'balance': '1000.5000000'}
            ]
        }

        client = StellarClient()
        balances = client.get_balance("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H")

        assert balances['native'] == '1000.5000000'
        assert balances['assets'] == []

    @patch('stellar_agent.client.Server')
    def test_get_balance_returns_multiple_assets(self, mock_server_class):
        """Test get_balance returns multiple assets."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.accounts().account_id().call.return_value = {
            'balances': [
                {'asset_type': 'native', 'balance': '500.0'},
                {
                    'asset_type': 'credit_alphanum4',
                    'asset_code': 'USDC',
                    'asset_issuer': 'GISSUER123',
                    'balance': '100.0'
                }
            ]
        }

        client = StellarClient()
        balances = client.get_balance("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H")

        assert balances['native'] == '500.0'
        assert len(balances['assets']) == 1
        assert balances['assets'][0]['asset_code'] == 'USDC'
        assert balances['assets'][0]['balance'] == '100.0'

    @patch('stellar_agent.client.Server')
    def test_get_balance_raises_error_on_not_found(self, mock_server_class):
        """Test get_balance raises PaymentError for non-existent account."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.accounts().account_id().call.side_effect = NotFoundError(Mock())

        client = StellarClient()

        with pytest.raises(PaymentError) as exc_info:
            client.get_balance("GDOESNOTEXIST")

        assert "does not exist" in str(exc_info.value)


class TestStellarClientTransactionHistory:
    """Test transaction history viewer (Issue #6)."""

    @patch('stellar_agent.client.Server')
    def test_get_transaction_history_returns_transactions(self, mock_server_class):
        """Test transaction history returns formatted transactions."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.transactions().for_account().limit().order().call.return_value = {
            '_embedded': {
                'records': [
                    {
                        'hash': 'abc123',
                        'created_at': '2026-02-27T10:00:00Z',
                        'source_account': 'GSOURCE',
                        'fee_charged': '100',
                        'operation_count': 1,
                        'memo': 'test'
                    }
                ]
            }
        }

        client = StellarClient()
        transactions = client.get_transaction_history("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H")

        assert len(transactions) == 1
        assert transactions[0]['hash'] == 'abc123'
        assert transactions[0]['memo'] == 'test'

    @patch('stellar_agent.client.Server')
    def test_get_transaction_history_raises_on_not_found(self, mock_server_class):
        """Test transaction history raises PaymentError for non-existent account."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.transactions().for_account().limit().order().call.side_effect = NotFoundError(Mock())

        client = StellarClient()

        with pytest.raises(PaymentError) as exc_info:
            client.get_transaction_history("GDOESNOTEXIST")

        assert "does not exist" in str(exc_info.value)


class TestStellarClientMultiSig:
    """Test multi-signature support (Issue #9)."""

    @patch('stellar_agent.client.Server')
    def test_add_signer_succeeds(self, mock_server_class):
        """Test adding a signer to an account."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server

        mock_account = Mock()
        mock_account.sequence = 1234567890
        mock_server.load_account.return_value = mock_account
        mock_server.submit_transaction.return_value = {'hash': 'signer_added_hash'}

        client = StellarClient()
        response = client.add_signer(
            "SACFBIKSA5AFZFVJGQFLJXEQ5Z7VM3CAHCHZDA5F4I5GJDXM7TKXQP74",  # Valid testnet secret
            "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            weight=1
        )

        assert response['hash'] == 'signer_added_hash'

    @patch('stellar_agent.client.Server')
    def test_add_signer_raises_on_not_found(self, mock_server_class):
        """Test add_signer raises PaymentError for non-existent account."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.load_account.side_effect = NotFoundError(Mock())

        client = StellarClient()

        with pytest.raises(PaymentError) as exc_info:
            client.add_signer(
                "SACFBIKSA5AFZFVJGQFLJXEQ5Z7VM3CAHCHZDA5F4I5GJDXM7TKXQP74",  # Valid testnet secret
                "GSIGNER123",
                weight=1
            )

        assert "not found" in str(exc_info.value)
