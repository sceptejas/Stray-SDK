"""Tests for StellarClient — balance and transaction history methods."""
import pytest
from unittest.mock import MagicMock, patch
from stellar_agent.client import StellarClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_ADDRESS = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"

MOCK_ACCOUNT_INFO = {
    "balances": [
        {
            "asset_type": "native",
            "balance": "95.0000000",
        },
        {
            "asset_type": "credit_alphanum4",
            "asset_code": "USDC",
            "balance": "10.5000000",
        },
    ]
}

MOCK_TRANSACTIONS = {
    "_embedded": {
        "records": [
            {
                "hash": "abc123def456abc123def456abc123def456abc123def456abc123def456abc1",
                "created_at": "2026-02-24T00:00:00Z",
                "successful": True,
                "fee_charged": "100",
                "operation_count": 1,
                "memo": "",
            },
            {
                "hash": "fff000fff000fff000fff000fff000fff000fff000fff000fff000fff000fff0",
                "created_at": "2026-02-23T23:00:00Z",
                "successful": False,
                "fee_charged": "100",
                "operation_count": 1,
                "memo": "test",
            },
        ]
    }
}


# ---------------------------------------------------------------------------
# get_balance
# ---------------------------------------------------------------------------

class TestGetBalance:
    """Tests for StellarClient.get_balance()."""

    def _make_client(self, account_info: dict) -> StellarClient:
        with patch("stellar_agent.client.Server"):
            client = StellarClient()
        client.get_account_info = MagicMock(return_value=account_info)
        return client

    def test_returns_xlm_balance(self):
        client = self._make_client(MOCK_ACCOUNT_INFO)
        balances = client.get_balance(VALID_ADDRESS)
        xlm = next((b for b in balances if b["asset"] == "XLM"), None)
        assert xlm is not None
        assert xlm["balance"] == "95.0000000"

    def test_returns_non_native_balance(self):
        client = self._make_client(MOCK_ACCOUNT_INFO)
        balances = client.get_balance(VALID_ADDRESS)
        usdc = next((b for b in balances if b["asset"] == "USDC"), None)
        assert usdc is not None
        assert usdc["balance"] == "10.5000000"

    def test_empty_balances(self):
        client = self._make_client({"balances": []})
        balances = client.get_balance(VALID_ADDRESS)
        assert balances == []

    def test_native_asset_mapped_to_xlm(self):
        client = self._make_client(MOCK_ACCOUNT_INFO)
        balances = client.get_balance(VALID_ADDRESS)
        asset_names = [b["asset"] for b in balances]
        assert "native" not in asset_names
        assert "XLM" in asset_names


# ---------------------------------------------------------------------------
# get_transaction_history
# ---------------------------------------------------------------------------

class TestGetTransactionHistory:
    """Tests for StellarClient.get_transaction_history()."""

    def _make_client(self, tx_data: dict) -> StellarClient:
        with patch("stellar_agent.client.Server") as mock_server_cls:
            mock_server = MagicMock()
            mock_server_cls.return_value = mock_server

            # Build a chainable mock: server.transactions().for_account().order().limit().call()
            mock_chain = MagicMock()
            mock_chain.call.return_value = tx_data
            mock_server.transactions.return_value.for_account.return_value \
                .order.return_value.limit.return_value = mock_chain

            client = StellarClient()
            client.server = mock_server
        return client

    def test_returns_list_of_transactions(self):
        client = self._make_client(MOCK_TRANSACTIONS)
        txs = client.get_transaction_history(VALID_ADDRESS, limit=10)
        assert len(txs) == 2

    def test_transaction_has_required_fields(self):
        client = self._make_client(MOCK_TRANSACTIONS)
        txs = client.get_transaction_history(VALID_ADDRESS, limit=10)
        required = {"hash", "created_at", "successful", "fee_charged", "operation_count", "memo"}
        for tx in txs:
            assert required.issubset(tx.keys())

    def test_successful_flag_is_boolean(self):
        client = self._make_client(MOCK_TRANSACTIONS)
        txs = client.get_transaction_history(VALID_ADDRESS)
        assert txs[0]["successful"] is True
        assert txs[1]["successful"] is False

    def test_limit_clamped_to_1_minimum(self):
        """Limit below 1 should be treated as 1."""
        with patch("stellar_agent.client.Server") as mock_server_cls:
            mock_server = MagicMock()
            mock_server_cls.return_value = mock_server
            mock_chain = MagicMock()
            mock_chain.call.return_value = {"_embedded": {"records": []}}
            mock_server.transactions.return_value.for_account.return_value \
                .order.return_value.limit.return_value = mock_chain

            client = StellarClient()
            client.server = mock_server
            client.get_transaction_history(VALID_ADDRESS, limit=0)

            # limit() should have been called with 1, not 0
            mock_server.transactions.return_value.for_account.return_value \
                .order.return_value.limit.assert_called_with(1)

    def test_limit_clamped_to_200_maximum(self):
        """Limit above 200 should be clamped to 200."""
        with patch("stellar_agent.client.Server") as mock_server_cls:
            mock_server = MagicMock()
            mock_server_cls.return_value = mock_server
            mock_chain = MagicMock()
            mock_chain.call.return_value = {"_embedded": {"records": []}}
            mock_server.transactions.return_value.for_account.return_value \
                .order.return_value.limit.return_value = mock_chain

            client = StellarClient()
            client.server = mock_server
            client.get_transaction_history(VALID_ADDRESS, limit=999)

            mock_server.transactions.return_value.for_account.return_value \
                .order.return_value.limit.assert_called_with(200)

    def test_empty_transaction_history(self):
        client = self._make_client({"_embedded": {"records": []}})
        txs = client.get_transaction_history(VALID_ADDRESS)
        assert txs == []
