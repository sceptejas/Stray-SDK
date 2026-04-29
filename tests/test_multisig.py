"""
Unit tests for MultiSigClient.

Covers:
- build_multisig_payment (happy path, validation, error handling)
- sign_transaction (happy path, invalid XDR)
- submit_transaction (success, bad_auth rejection, balance rejection)
- configure_multisig_account (happy path, account-not-found)
- get_signers / get_thresholds (happy path, not-found)
- count_signatures (happy path, invalid XDR)
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from stellar_agent.multisig import MultiSigClient, _public_from_secret, _keypair_from_secret
from stellar_sdk.exceptions import NotFoundError, BadRequestError


# ---------------------------------------------------------------------------
# Shared constants (use obviously-fake-but-format-correct keys for tests)
# ---------------------------------------------------------------------------

FAKE_SOURCE_SECRET = "SBKWQ3BSIQPGNIDBNZRQFGBJ5QU3I34WMO4JHBGVIPUJLCVLH6FPAVGE"  # 56 chars, starts with S
FAKE_CO_SIGNER_SECRET = "SCNFNQKZTESXZPDFQ3CQFRMWTXNQY5E4FKYLHCTZQXSAZB7YHMPWF7U"
FAKE_DEST_PUBLIC = "GDQOE23CFSUMSVQK4Y5JHPPYK73VYCNHZHA7ENKCV37P6SUEO6XQBKPP"  # 56 chars, starts with G

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_config():
    """Patch the module-level config singleton used by MultiSigClient."""
    with patch("stellar_agent.multisig.config") as mock_conf:
        mock_conf.horizon_url = "https://horizon-testnet.stellar.org"
        mock_conf.network_passphrase = "Test SDF Network ; September 2015"
        yield mock_conf


@pytest.fixture
def mock_server_class(mock_config):
    """Patch stellar_sdk.Server so no real network calls are made."""
    with patch("stellar_agent.multisig.Server") as cls:
        yield cls


@pytest.fixture
def client(mock_server_class):
    """Return a MultiSigClient with a mocked Server."""
    return MultiSigClient()


# ---------------------------------------------------------------------------
# Helper: build a minimal XDR using real SDK objects (no network)
# ---------------------------------------------------------------------------

def _make_real_xdr():
    """
    Build a minimal, locally-signed XDR using the actual Stellar SDK
    (no Horizon call needed) so we can test XDR parsing methods.
    """
    from stellar_sdk import Keypair, TransactionBuilder, Network, Asset
    from stellar_sdk.operation import Payment
    from stellar_sdk.account import Account

    passphrase = "Test SDF Network ; September 2015"
    kp = Keypair.random()
    account = Account(kp.public_key, sequence=1)

    dest_kp = Keypair.random()
    builder = TransactionBuilder(
        source_account=account,
        network_passphrase=passphrase,
        base_fee=100,
    )
    builder.append_operation(
        Payment(
            destination=dest_kp.public_key,
            asset=Asset.native(),
            amount="10",
        )
    )
    builder.set_timeout(30)
    tx = builder.build()
    tx.sign(kp)
    return tx.to_xdr(), kp, passphrase


# ---------------------------------------------------------------------------
# Tests: _keypair_from_secret helper
# ---------------------------------------------------------------------------

class TestKeypairHelper:
    def test_invalid_secret_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid secret key"):
            _keypair_from_secret("NOT_A_VALID_SECRET")

    def test_valid_secret_returns_keypair(self):
        from stellar_sdk import Keypair
        kp = Keypair.random()
        result = _keypair_from_secret(kp.secret)
        assert result.public_key == kp.public_key


# ---------------------------------------------------------------------------
# Tests: build_multisig_payment
# ---------------------------------------------------------------------------

class TestBuildMultisigPayment:
    def test_raises_on_zero_amount(self, client):
        with pytest.raises(ValueError, match="amount must be greater than zero"):
            client.build_multisig_payment(
                source_secret=FAKE_SOURCE_SECRET,
                destination_public=FAKE_DEST_PUBLIC,
                amount=0,
            )

    def test_raises_on_negative_amount(self, client):
        with pytest.raises(ValueError, match="amount must be greater than zero"):
            client.build_multisig_payment(
                source_secret=FAKE_SOURCE_SECRET,
                destination_public=FAKE_DEST_PUBLIC,
                amount=-5,
            )

    def test_raises_on_invalid_source_secret(self, client):
        with pytest.raises(ValueError, match="Invalid secret key"):
            client.build_multisig_payment(
                source_secret="BADSECRET",
                destination_public=FAKE_DEST_PUBLIC,
                amount=10,
            )

    def test_raises_runtime_on_account_not_found(self, mock_server_class):
        mock_server = mock_server_class.return_value
        mock_response = Mock()
        mock_response.status_code = 404
        mock_server.load_account.side_effect = NotFoundError(mock_response)
        client = MultiSigClient()

        from stellar_sdk import Keypair
        kp = Keypair.random()
        with pytest.raises(RuntimeError, match="not found on the network"):
            client.build_multisig_payment(
                source_secret=kp.secret,
                destination_public=FAKE_DEST_PUBLIC,
                amount=10,
            )

    def test_raises_runtime_on_generic_load_failure(self, mock_server_class):
        mock_server = mock_server_class.return_value
        mock_server.load_account.side_effect = Exception("network timeout")
        client = MultiSigClient()

        from stellar_sdk import Keypair
        kp = Keypair.random()
        with pytest.raises(RuntimeError, match="Failed to load source account"):
            client.build_multisig_payment(
                source_secret=kp.secret,
                destination_public=FAKE_DEST_PUBLIC,
                amount=10,
            )

    def test_returns_xdr_string_with_no_extra_signers(self, mock_server_class):
        from stellar_sdk import Keypair, Account
        from stellar_sdk.account import Account as StellarAccount

        source_kp = Keypair.random()
        dest_kp = Keypair.random()

        mock_server = mock_server_class.return_value
        mock_server.load_account.return_value = StellarAccount(
            source_kp.public_key, sequence=1
        )

        client = MultiSigClient()
        xdr = client.build_multisig_payment(
            source_secret=source_kp.secret,
            destination_public=dest_kp.public_key,
            amount=10,
        )

        assert isinstance(xdr, str)
        assert len(xdr) > 0

    def test_returns_xdr_with_multiple_signers(self, mock_server_class):
        from stellar_sdk import Keypair, Account
        from stellar_sdk.account import Account as StellarAccount

        source_kp = Keypair.random()
        co_kp1 = Keypair.random()
        co_kp2 = Keypair.random()
        dest_kp = Keypair.random()

        mock_server = mock_server_class.return_value
        mock_server.load_account.return_value = StellarAccount(
            source_kp.public_key, sequence=1
        )

        client = MultiSigClient()
        xdr = client.build_multisig_payment(
            source_secret=source_kp.secret,
            destination_public=dest_kp.public_key,
            amount=25,
            signers=[co_kp1.secret, co_kp2.secret],
        )

        # 3 signatures: source + 2 co-signers
        sig_count = client.count_signatures(xdr)
        assert sig_count == 3

    def test_memo_is_truncated_to_28_bytes(self, mock_server_class):
        from stellar_sdk import Keypair
        from stellar_sdk.account import Account as StellarAccount
        from stellar_sdk import TransactionEnvelope

        source_kp = Keypair.random()
        dest_kp = Keypair.random()

        mock_server = mock_server_class.return_value
        mock_server.load_account.return_value = StellarAccount(
            source_kp.public_key, sequence=1
        )

        client = MultiSigClient()
        long_memo = "A" * 100
        xdr = client.build_multisig_payment(
            source_secret=source_kp.secret,
            destination_public=dest_kp.public_key,
            amount=10,
            memo=long_memo,
        )
        # Should not raise; memo accepted by SDK within 28-byte slice
        assert isinstance(xdr, str)


# ---------------------------------------------------------------------------
# Tests: sign_transaction
# ---------------------------------------------------------------------------

class TestSignTransaction:
    def test_adds_signature_to_envelope(self, mock_server_class):
        from stellar_sdk import Keypair
        xdr, original_kp, passphrase = _make_real_xdr()

        client = MultiSigClient()
        initial_count = client.count_signatures(xdr)

        new_kp = Keypair.random()
        updated_xdr = client.sign_transaction(xdr, new_kp.secret)
        new_count = client.count_signatures(updated_xdr)

        assert new_count == initial_count + 1

    def test_raises_value_error_on_invalid_xdr(self, client):
        from stellar_sdk import Keypair
        kp = Keypair.random()
        with pytest.raises(ValueError, match="Invalid transaction XDR"):
            client.sign_transaction("NOT_VALID_XDR", kp.secret)

    def test_raises_value_error_on_invalid_secret(self, client):
        xdr, _, _ = _make_real_xdr()
        with pytest.raises(ValueError, match="Invalid secret key"):
            client.sign_transaction(xdr, "BADSECRET")


# ---------------------------------------------------------------------------
# Tests: submit_transaction
# ---------------------------------------------------------------------------

class TestSubmitTransaction:
    def test_successful_submission_returns_response(self, mock_server_class):
        xdr, _, _ = _make_real_xdr()
        expected = {"hash": "abc123", "ledger": 42}

        mock_server = mock_server_class.return_value
        mock_server.submit_transaction.return_value = expected

        client = MultiSigClient()
        result = client.submit_transaction(xdr)

        assert result == expected
        mock_server.submit_transaction.assert_called_once()

    def test_bad_auth_raises_descriptive_runtime_error(self, mock_server_class):
        xdr, _, _ = _make_real_xdr()

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "tx_bad_auth"

        mock_server = mock_server_class.return_value
        mock_server.submit_transaction.side_effect = BadRequestError(mock_response)

        client = MultiSigClient()
        with pytest.raises(RuntimeError, match="insufficient signatures"):
            client.submit_transaction(xdr)

    def test_insufficient_balance_raises_descriptive_runtime_error(
        self, mock_server_class
    ):
        xdr, _, _ = _make_real_xdr()

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "insufficient balance"

        mock_server = mock_server_class.return_value
        mock_server.submit_transaction.side_effect = BadRequestError(mock_response)

        client = MultiSigClient()
        with pytest.raises(RuntimeError, match="insufficient balance"):
            client.submit_transaction(xdr)

    def test_invalid_xdr_raises_value_error(self, client):
        with pytest.raises(ValueError, match="Invalid transaction XDR"):
            client.submit_transaction("GARBLED_XDR")

    def test_generic_exception_raises_runtime_error(self, mock_server_class):
        xdr, _, _ = _make_real_xdr()

        mock_server = mock_server_class.return_value
        mock_server.submit_transaction.side_effect = Exception("connection reset")

        client = MultiSigClient()
        with pytest.raises(RuntimeError, match="Unexpected error"):
            client.submit_transaction(xdr)


# ---------------------------------------------------------------------------
# Tests: configure_multisig_account
# ---------------------------------------------------------------------------

class TestConfigureMultisigAccount:
    def test_submits_set_options_transaction(self, mock_server_class):
        from stellar_sdk import Keypair
        from stellar_sdk.account import Account as StellarAccount

        source_kp = Keypair.random()
        co_kp = Keypair.random()

        mock_server = mock_server_class.return_value
        mock_server.load_account.return_value = StellarAccount(
            source_kp.public_key, sequence=1
        )
        mock_server.submit_transaction.return_value = {"hash": "set_options_hash"}

        client = MultiSigClient()
        result = client.configure_multisig_account(
            source_secret=source_kp.secret,
            co_signer_public_keys=[co_kp.public_key],
        )

        mock_server.submit_transaction.assert_called_once()
        assert result == {"hash": "set_options_hash"}

    def test_account_not_found_raises_runtime_error(self, mock_server_class):
        mock_server = mock_server_class.return_value
        mock_response = Mock()
        mock_response.status_code = 404
        mock_server.load_account.side_effect = NotFoundError(mock_response)

        from stellar_sdk import Keypair
        kp = Keypair.random()

        client = MultiSigClient()
        with pytest.raises(RuntimeError, match="not found"):
            client.configure_multisig_account(
                source_secret=kp.secret,
                co_signer_public_keys=[],
            )

    def test_bad_request_on_submit_raises_runtime_error(self, mock_server_class):
        from stellar_sdk import Keypair
        from stellar_sdk.account import Account as StellarAccount

        source_kp = Keypair.random()

        mock_server = mock_server_class.return_value
        mock_server.load_account.return_value = StellarAccount(
            source_kp.public_key, sequence=1
        )
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "tx_failed"
        mock_server.submit_transaction.side_effect = BadRequestError(mock_response)

        client = MultiSigClient()
        with pytest.raises(RuntimeError, match="Failed to configure multisig account"):
            client.configure_multisig_account(
                source_secret=source_kp.secret,
                co_signer_public_keys=[],
            )


# ---------------------------------------------------------------------------
# Tests: get_signers
# ---------------------------------------------------------------------------

class TestGetSigners:
    def test_returns_signers_list(self, mock_server_class):
        expected_signers = [
            {"key": "GABC...", "weight": 1, "type": "ed25519_public_key"},
            {"key": "GDEF...", "weight": 1, "type": "ed25519_public_key"},
        ]
        mock_server = mock_server_class.return_value
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_server.accounts.return_value = mock_accounts
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.return_value = {"signers": expected_signers}

        client = MultiSigClient()
        result = client.get_signers("GABC...")

        assert result == expected_signers

    def test_not_found_raises_runtime_error(self, mock_server_class):
        mock_server = mock_server_class.return_value
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_server.accounts.return_value = mock_accounts
        mock_accounts.account_id.return_value = mock_account_id
        mock_response = Mock()
        mock_response.status_code = 404
        mock_account_id.call.side_effect = NotFoundError(mock_response)

        client = MultiSigClient()
        with pytest.raises(RuntimeError, match="not found"):
            client.get_signers("GABC...")

    def test_generic_error_raises_runtime_error(self, mock_server_class):
        mock_server = mock_server_class.return_value
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_server.accounts.return_value = mock_accounts
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.side_effect = Exception("timeout")

        client = MultiSigClient()
        with pytest.raises(RuntimeError, match="Failed to fetch account signers"):
            client.get_signers("GABC...")


# ---------------------------------------------------------------------------
# Tests: get_thresholds
# ---------------------------------------------------------------------------

class TestGetThresholds:
    def test_returns_threshold_dict(self, mock_server_class):
        mock_server = mock_server_class.return_value
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_server.accounts.return_value = mock_accounts
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.return_value = {
            "thresholds": {
                "low_threshold": 1,
                "med_threshold": 2,
                "high_threshold": 2,
            }
        }

        client = MultiSigClient()
        result = client.get_thresholds("GABC...")

        assert result == {
            "low_threshold": 1,
            "med_threshold": 2,
            "high_threshold": 2,
        }

    def test_missing_thresholds_key_returns_zeros(self, mock_server_class):
        mock_server = mock_server_class.return_value
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_server.accounts.return_value = mock_accounts
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.return_value = {}  # no 'thresholds' key

        client = MultiSigClient()
        result = client.get_thresholds("GABC...")

        assert result == {
            "low_threshold": 0,
            "med_threshold": 0,
            "high_threshold": 0,
        }

    def test_not_found_raises_runtime_error(self, mock_server_class):
        mock_server = mock_server_class.return_value
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_server.accounts.return_value = mock_accounts
        mock_accounts.account_id.return_value = mock_account_id
        mock_response = Mock()
        mock_response.status_code = 404
        mock_account_id.call.side_effect = NotFoundError(mock_response)

        client = MultiSigClient()
        with pytest.raises(RuntimeError, match="not found"):
            client.get_thresholds("GABC...")


# ---------------------------------------------------------------------------
# Tests: count_signatures
# ---------------------------------------------------------------------------

class TestCountSignatures:
    def test_counts_single_signature(self, client):
        xdr, _, _ = _make_real_xdr()
        count = client.count_signatures(xdr)
        assert count == 1

    def test_counts_multiple_signatures(self, mock_server_class):
        from stellar_sdk import Keypair
        xdr, _, _ = _make_real_xdr()

        client = MultiSigClient()
        kp1 = Keypair.random()
        kp2 = Keypair.random()
        xdr = client.sign_transaction(xdr, kp1.secret)
        xdr = client.sign_transaction(xdr, kp2.secret)

        assert client.count_signatures(xdr) == 3

    def test_invalid_xdr_raises_value_error(self, client):
        with pytest.raises(ValueError, match="Invalid transaction XDR"):
            client.count_signatures("THIS_IS_NOT_XDR")


# ---------------------------------------------------------------------------
# Integration-style: full pass-around workflow
# ---------------------------------------------------------------------------

class TestPassAroundWorkflow:
    """
    Simulate the full 3-step multisig workflow:
      1. Initiator builds & signs.
      2. Co-signer signs.
      3. Anyone submits.
    """

    def test_full_workflow(self, mock_server_class):
        from stellar_sdk import Keypair
        from stellar_sdk.account import Account as StellarAccount

        source_kp = Keypair.random()
        co_kp = Keypair.random()
        dest_kp = Keypair.random()

        mock_server = mock_server_class.return_value
        mock_server.load_account.return_value = StellarAccount(
            source_kp.public_key, sequence=1
        )
        mock_server.submit_transaction.return_value = {
            "hash": "workflow_tx_hash",
            "ledger": 100,
        }

        client = MultiSigClient()

        # Step 1: initiator builds (1 sig)
        xdr = client.build_multisig_payment(
            source_secret=source_kp.secret,
            destination_public=dest_kp.public_key,
            amount=15,
        )
        assert client.count_signatures(xdr) == 1

        # Step 2: co-signer adds their sig (2 sigs total)
        xdr = client.sign_transaction(xdr, co_kp.secret)
        assert client.count_signatures(xdr) == 2

        # Step 3: submit
        result = client.submit_transaction(xdr)
        assert result["hash"] == "workflow_tx_hash"
        mock_server.submit_transaction.assert_called_once()
