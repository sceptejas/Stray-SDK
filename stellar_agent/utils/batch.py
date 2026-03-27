"""Batch payment utilities for Stellar Agent."""
import csv
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .validators import is_valid_stellar_address, is_valid_amount


@dataclass
class BatchEntry:
    """A single row parsed from a batch CSV file."""
    destination: str
    amount: float
    memo: Optional[str] = None
    row_number: int = 0


@dataclass
class BatchPaymentResult:
    """Result of a single payment attempt within a batch."""
    entry: BatchEntry
    success: bool
    tx_hash: str = ""
    error: str = ""


@dataclass
class BatchSummary:
    """Aggregated results after processing an entire batch."""
    results: List[BatchPaymentResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        return self.total - self.succeeded

    @property
    def total_xlm_sent(self) -> float:
        return sum(r.entry.amount for r in self.results if r.success)


def parse_batch_csv(file_path: str) -> Tuple[List[BatchEntry], List[str]]:
    """
    Parse a CSV file into BatchEntry objects.

    Expected CSV format (header row required):
        destination,amount,memo
        GABC...,10.5,Payment note
        GXYZ...,5.0,

    Args:
        file_path: Absolute or relative path to the CSV file.

    Returns:
        Tuple of (valid_entries, error_messages).
        error_messages contains per-row validation problems.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Batch file not found: {file_path}")

    entries: List[BatchEntry] = []
    errors: List[str] = []

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None or "destination" not in reader.fieldnames or "amount" not in reader.fieldnames:
            raise ValueError(
                "CSV must contain at least 'destination' and 'amount' columns as headers."
            )

        for row_number, row in enumerate(reader, start=2):  # 2 = first data row
            destination = (row.get("destination") or "").strip()
            amount_str = (row.get("amount") or "").strip()
            memo = (row.get("memo") or "").strip() or None

            # Validate destination
            if not is_valid_stellar_address(destination):
                errors.append(
                    f"Row {row_number}: Invalid Stellar address '{destination}'"
                )
                continue

            # Validate amount
            try:
                amount = float(amount_str)
            except ValueError:
                errors.append(
                    f"Row {row_number}: Invalid amount '{amount_str}' — must be a number"
                )
                continue

            if not is_valid_amount(amount):
                errors.append(
                    f"Row {row_number}: Amount must be positive, got '{amount}'"
                )
                continue

            entries.append(
                BatchEntry(
                    destination=destination,
                    amount=amount,
                    memo=memo,
                    row_number=row_number,
                )
            )

    return entries, errors


def print_batch_summary(summary: BatchSummary) -> None:
    """Print a formatted summary table to stdout."""
    print(f"\n--- Batch Payment Summary ---")
    print(f"  Total    : {summary.total}")
    print(f"  Succeeded: {summary.succeeded}")
    print(f"  Failed   : {summary.failed}")
    print(f"  XLM Sent : {summary.total_xlm_sent:.7f}")

    if summary.failed:
        print("\nFailed payments:")
        for r in summary.results:
            if not r.success:
                dst = r.entry.destination
                dst_short = f"{dst[:6]}...{dst[-6:]}" if len(dst) > 12 else dst
                print(f"  Row {r.entry.row_number}: {dst_short} | {r.entry.amount} XLM | {r.error}")
