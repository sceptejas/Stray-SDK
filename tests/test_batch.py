"""Tests for batch payment utilities."""
import csv
import os
import pytest
from unittest.mock import MagicMock, patch
from stellar_agent.utils.batch import (
    BatchEntry,
    BatchPaymentResult,
    BatchSummary,
    parse_batch_csv,
    print_batch_summary,
)
from stellar_agent.client import StellarClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_ADDR_1 = "GC3AJP5PFWEK6RFDCHKSLZ5I46MR6NV4SBEBYK35GYWNCOW2JOYM3HIG"
VALID_ADDR_2 = "GDCI46PMOQRPV6LKDWD64VRXVH63TVPA2W2YR5CPQ5UTIWPFTYM2W7G6"


def make_csv(tmp_path, rows, header="destination,amount,memo"):
    fpath = tmp_path / "batch.csv"
    with open(fpath, "w", newline="", encoding="utf-8") as f:
        f.write(header + "\n")
        for row in rows:
            f.write(",".join(str(c) for c in row) + "\n")
    return str(fpath)


# ---------------------------------------------------------------------------
# parse_batch_csv
# ---------------------------------------------------------------------------

class TestParseBatchCsv:
    def test_valid_rows_parsed(self, tmp_path):
        fpath = make_csv(tmp_path, [
            [VALID_ADDR_1, "10.0", "memo1"],
            [VALID_ADDR_2, "5.5", ""],
        ])
        entries, errors = parse_batch_csv(fpath)
        assert len(entries) == 2
        assert errors == []
        assert entries[0].destination == VALID_ADDR_1
        assert entries[0].amount == 10.0
        assert entries[0].memo == "memo1"
        assert entries[1].memo is None

    def test_invalid_address_skipped(self, tmp_path):
        fpath = make_csv(tmp_path, [
            ["NOTANADDRESS", "5.0", ""],
            [VALID_ADDR_1, "3.0", ""],
        ])
        entries, errors = parse_batch_csv(fpath)
        assert len(entries) == 1
        assert len(errors) == 1
        assert "Invalid Stellar address" in errors[0]

    def test_invalid_amount_skipped(self, tmp_path):
        fpath = make_csv(tmp_path, [
            [VALID_ADDR_1, "notanumber", ""],
        ])
        entries, errors = parse_batch_csv(fpath)
        assert len(entries) == 0
        assert "Invalid amount" in errors[0]

    def test_zero_amount_skipped(self, tmp_path):
        fpath = make_csv(tmp_path, [
            [VALID_ADDR_1, "0", ""],
        ])
        entries, errors = parse_batch_csv(fpath)
        assert len(entries) == 0
        assert "positive" in errors[0]

    def test_negative_amount_skipped(self, tmp_path):
        fpath = make_csv(tmp_path, [
            [VALID_ADDR_1, "-1", ""],
        ])
        entries, errors = parse_batch_csv(fpath)
        assert len(entries) == 0

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_batch_csv("/nonexistent/path/batch.csv")

    def test_missing_required_columns(self, tmp_path):
        fpath = make_csv(tmp_path, [["10.0"]], header="amount")
        with pytest.raises(ValueError, match="destination"):
            parse_batch_csv(fpath)

    def test_row_numbers_assigned(self, tmp_path):
        fpath = make_csv(tmp_path, [
            [VALID_ADDR_1, "1.0", ""],
            [VALID_ADDR_2, "2.0", ""],
        ])
        entries, _ = parse_batch_csv(fpath)
        assert entries[0].row_number == 2
        assert entries[1].row_number == 3

    def test_empty_file_returns_empty(self, tmp_path):
        fpath = make_csv(tmp_path, [])
        entries, errors = parse_batch_csv(fpath)
        assert entries == []
        assert errors == []


# ---------------------------------------------------------------------------
# BatchSummary
# ---------------------------------------------------------------------------

class TestBatchSummary:
    def _make_summary(self, successes, failures):
        results = []
        for i in range(successes):
            entry = BatchEntry(destination=VALID_ADDR_1, amount=float(i + 1))
            results.append(BatchPaymentResult(entry=entry, success=True, tx_hash=f"hash{i}"))
        for i in range(failures):
            entry = BatchEntry(destination=VALID_ADDR_2, amount=1.0)
            results.append(BatchPaymentResult(entry=entry, success=False, error="err"))
        s = BatchSummary()
        s.results = results
        return s

    def test_totals(self):
        s = self._make_summary(3, 2)
        assert s.total == 5
        assert s.succeeded == 3
        assert s.failed == 2

    def test_total_xlm_sent(self):
        s = self._make_summary(3, 0)
        # amounts: 1.0 + 2.0 + 3.0
        assert s.total_xlm_sent == 6.0

    def test_empty_summary(self):
        s = BatchSummary()
        assert s.total == 0
        assert s.succeeded == 0
        assert s.total_xlm_sent == 0.0


# ---------------------------------------------------------------------------
# StellarClient.send_batch_payments
# ---------------------------------------------------------------------------

class TestSendBatchPayments:
    def _make_client(self):
        with patch("stellar_agent.client.Server"):
            return StellarClient()

    def test_all_succeed(self):
        client = self._make_client()
        entries = [
            BatchEntry(destination=VALID_ADDR_1, amount=1.0, row_number=2),
            BatchEntry(destination=VALID_ADDR_2, amount=2.0, row_number=3),
        ]
        with patch.object(client, "send_payment", return_value={"hash": "txhash123"}):
            summary = client.send_batch_payments("SSECRET", entries)
        assert summary.succeeded == 2
        assert summary.failed == 0

    def test_partial_failure(self):
        client = self._make_client()
        entries = [
            BatchEntry(destination=VALID_ADDR_1, amount=1.0, row_number=2),
            BatchEntry(destination=VALID_ADDR_2, amount=2.0, row_number=3),
        ]

        def side_effect(source_secret, destination_public, amount, memo=None):
            if destination_public == VALID_ADDR_2:
                raise RuntimeError("Insufficient balance")
            return {"hash": "txhash123"}

        with patch.object(client, "send_payment", side_effect=side_effect):
            summary = client.send_batch_payments("SSECRET", entries)

        assert summary.succeeded == 1
        assert summary.failed == 1
        assert "Insufficient balance" in summary.results[1].error

    def test_stop_on_error(self):
        client = self._make_client()
        entries = [
            BatchEntry(destination=VALID_ADDR_1, amount=1.0, row_number=2),
            BatchEntry(destination=VALID_ADDR_2, amount=2.0, row_number=3),
        ]
        with patch.object(client, "send_payment", side_effect=RuntimeError("fail")):
            summary = client.send_batch_payments("SSECRET", entries, stop_on_error=True)
        # Only the first entry is attempted
        assert summary.total == 1
        assert summary.failed == 1

    def test_empty_entries(self):
        client = self._make_client()
        with patch.object(client, "send_payment") as mock_send:
            summary = client.send_batch_payments("SSECRET", [])
        mock_send.assert_not_called()
        assert summary.total == 0
