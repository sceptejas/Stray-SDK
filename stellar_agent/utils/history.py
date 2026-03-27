"""Transaction history management for Stellar Agent."""
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "transaction_history.json")


class TransactionHistory:
    """Manages persistent transaction history stored as JSON."""

    def __init__(self, history_file: str = HISTORY_FILE):
        self.history_file = os.path.abspath(history_file)

    def _load(self) -> List[Dict[str, Any]]:
        """Load all records from the history file."""
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, records: List[Dict[str, Any]]) -> None:
        """Persist records to the history file."""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    def record(
        self,
        source: str,
        destination: str,
        amount: float,
        tx_hash: str,
        ledger: Optional[int] = None,
        network: str = "testnet",
        memo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Save a successful transaction to history.

        Args:
            source: Source public key
            destination: Destination public key
            amount: Amount of XLM sent
            tx_hash: Transaction hash returned by Horizon
            ledger: Ledger number the transaction was included in
            network: Network identifier (testnet / mainnet)
            memo: Optional memo attached to the transaction

        Returns:
            The saved record dictionary
        """
        record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "destination": destination,
            "amount_xlm": amount,
            "tx_hash": tx_hash,
            "ledger": ledger,
            "network": network,
            "memo": memo,
        }
        records = self._load()
        records.append(record)
        self._save(records)
        return record

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all transaction records, newest first."""
        return list(reversed(self._load()))

    def get_by_source(self, source: str) -> List[Dict[str, Any]]:
        """Return transactions sent from a specific account."""
        return [r for r in self.get_all() if r.get("source") == source]

    def get_by_destination(self, destination: str) -> List[Dict[str, Any]]:
        """Return transactions sent to a specific account."""
        return [r for r in self.get_all() if r.get("destination") == destination]

    def clear(self) -> int:
        """Clear all history. Returns the number of deleted records."""
        records = self._load()
        count = len(records)
        self._save([])
        return count


def format_record(record: Dict[str, Any], index: int) -> str:
    """Return a human-readable string for a single history record."""
    ts = record.get("timestamp", "unknown")
    src = record.get("source", "")
    dst = record.get("destination", "")
    amount = record.get("amount_xlm", 0)
    tx_hash = record.get("tx_hash", "")
    ledger = record.get("ledger")
    network = record.get("network", "")
    memo = record.get("memo")

    src_short = f"{src[:6]}...{src[-6:]}" if len(src) > 12 else src
    dst_short = f"{dst[:6]}...{dst[-6:]}" if len(dst) > 12 else dst
    hash_short = f"{tx_hash[:10]}...{tx_hash[-10:]}" if len(tx_hash) > 20 else tx_hash

    lines = [
        f"  #{index}  {ts}",
        f"       From   : {src_short}",
        f"       To     : {dst_short}",
        f"       Amount : {amount} XLM",
        f"       Hash   : {hash_short}",
    ]
    if ledger:
        lines.append(f"       Ledger : {ledger}")
    if network:
        lines.append(f"       Network: {network}")
    if memo:
        lines.append(f"       Memo   : {memo}")
    return "\n".join(lines)
