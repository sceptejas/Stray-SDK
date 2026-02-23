"""Stellar blockchain client for payment operations."""
from stellar_sdk import Server, Keypair, TransactionBuilder, Asset
from stellar_sdk.operation import Payment
from typing import Dict, Any, List, Optional
from .config import config

class StellarClient:
    """Client for interacting with Stellar blockchain."""
    
    def __init__(self):
        self.server = Server(config.horizon_url)
    
    def get_account_info(self, account_id: str) -> Dict[str, Any]:
        """
        Fetch account information from Horizon.
        
        Args:
            account_id: Public key of the account
            
        Returns:
            Account information dictionary
        """
        response = self.server.accounts().account_id(account_id).call()
        return response

    def get_balance(self, account_id: str) -> List[Dict[str, str]]:
        """
        Fetch all asset balances for an account.

        Args:
            account_id: Public key of the account

        Returns:
            List of dicts with 'asset' and 'balance' keys
        """
        info = self.get_account_info(account_id)
        balances = []
        for b in info.get("balances", []):
            asset = b.get("asset_type")
            if asset == "native":
                asset = "XLM"
            else:
                asset = b.get("asset_code", "UNKNOWN")
            balances.append({"asset": asset, "balance": b.get("balance", "0")})
        return balances

    def get_transaction_history(
        self, account_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent transactions for an account.

        Args:
            account_id: Public key of the account
            limit: Number of transactions to retrieve (default 10, max 200)

        Returns:
            List of transaction summary dicts
        """
        limit = max(1, min(limit, 200))
        records = (
            self.server.transactions()
            .for_account(account_id)
            .order(desc=True)
            .limit(limit)
            .call()
            .get("_embedded", {})
            .get("records", [])
        )
        result = []
        for tx in records:
            result.append(
                {
                    "hash": tx.get("hash", ""),
                    "created_at": tx.get("created_at", ""),
                    "successful": tx.get("successful", False),
                    "fee_charged": tx.get("fee_charged", "0"),
                    "operation_count": tx.get("operation_count", 0),
                    "memo": tx.get("memo", ""),
                }
            )
        return result

    def send_payment(
        self, 
        source_secret: str, 
        destination_public: str, 
        amount: float
    ) -> Dict[str, Any]:
        """
        Send XLM payment to a destination address.
        
        Args:
            source_secret: Secret key of the source account
            destination_public: Public key of the destination account
            amount: Amount of XLM to send
            
        Returns:
            Transaction response dictionary
        """
        source_keypair = Keypair.from_secret(source_secret)
        source_account = self.server.load_account(source_keypair.public_key)

        transaction = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=config.network_passphrase,
                base_fee=100,
            )
            .append_operation(
                Payment(
                    destination=destination_public,
                    asset=Asset.native(),
                    amount=str(amount)
                )
            )
            .set_timeout(30)
            .build()
        )

        transaction.sign(source_keypair)
        response = self.server.submit_transaction(transaction)
        return response
