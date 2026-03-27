"""Tests for transaction history module."""
import json
import os
import pytest
from decimal import Decimal
from stellar_agent.utils.history import TransactionHistory, format_record


@pytest.fixture
def history(tmp_path):
    """TransactionHistory instance backed by a temporary file."""
    return TransactionHistory(history_file=str(tmp_path / "history.json"))


class TestTransactionHistory:
    def test_record_creates_file(self, history, tmp_path):
        history.record(
            source="GABC123",
            destination="GXYZ789",
            amount=10.0,
            tx_hash="abc123hash",
        )
        assert os.path.exists(history.history_file)

    def test_record_saves_fields(self, history):
        history.record(
            source="GABC",
            destination="GXYZ",
            amount=5.5,
            tx_hash="txhash1",
            ledger=1234,
            network="testnet",
            memo="test memo",
        )
        records = history.get_all()
        assert len(records) == 1
        r = records[0]
        assert r["source"] == "GABC"
        assert r["destination"] == "GXYZ"
        assert r["amount_xlm"] == 5.5
        assert r["tx_hash"] == "txhash1"
        assert r["ledger"] == 1234
        assert r["network"] == "testnet"
        assert r["memo"] == "test memo"

    def test_get_all_newest_first(self, history):
        history.record("GA", "GB", 1.0, "hash1")
        history.record("GA", "GB", 2.0, "hash2")
        records = history.get_all()
        assert records[0]["tx_hash"] == "hash2"
        assert records[1]["tx_hash"] == "hash1"

    def test_get_all_empty(self, history):
        assert history.get_all() == []

    def test_get_by_source(self, history):
        history.record("GSRC1", "GDST", 1.0, "h1")
        history.record("GSRC2", "GDST", 2.0, "h2")
        results = history.get_by_source("GSRC1")
        assert len(results) == 1
        assert results[0]["tx_hash"] == "h1"

    def test_get_by_destination(self, history):
        history.record("GSRC", "GDST1", 1.0, "h1")
        history.record("GSRC", "GDST2", 2.0, "h2")
        results = history.get_by_destination("GDST2")
        assert len(results) == 1
        assert results[0]["tx_hash"] == "h2"

    def test_clear(self, history):
        history.record("GA", "GB", 1.0, "h1")
        history.record("GA", "GB", 2.0, "h2")
        deleted = history.clear()
        assert deleted == 2
        assert history.get_all() == []

    def test_multiple_records_persist(self, history):
        for i in range(5):
            history.record("GA", "GB", float(i), f"hash{i}")
        assert len(history.get_all()) == 5

    def test_corrupted_file_returns_empty(self, tmp_path):
        fpath = tmp_path / "history.json"
        fpath.write_text("not valid json", encoding="utf-8")
        h = TransactionHistory(history_file=str(fpath))
        assert h.get_all() == []


class TestFormatRecord:
    def test_format_includes_key_fields(self):
        record = {
            "timestamp": "2026-03-27T10:00:00+00:00",
            "source": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "destination": "GBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
            "amount_xlm": 10.0,
            "tx_hash": "abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdef",
            "ledger": 999,
            "network": "testnet",
            "memo": None,
        }
        output = format_record(record, 1)
        assert "10.0 XLM" in output
        assert "999" in output
        assert "testnet" in output
        assert "#1" in output
