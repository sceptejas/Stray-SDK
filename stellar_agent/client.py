"""Stellar blockchain client for payment operations."""
from stellar_sdk import Server, Keypair, TransactionBuilder, Asset, Transaction, Signer
from stellar_sdk.operation import Payment, SetOptions
from stellar_sdk.exceptions import NotFoundError, BadRequestError
from typing import Dict, Any, Optional, List
from .config import config
from .utils.validators import format_stellar_amount


class PaymentError(Exception):
    """Custom exception for payment-related errors with sanitized messages."""
    pass


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

    def account_exists(self, account_id: str) -> bool:
        """
        Check if an account exists on the Stellar network.

        This is a pre-flight check to validate the destination before
        building and signing a transaction.

        Args:
            account_id: Public key of the account to check

        Returns:
            True if account exists, False otherwise
        """
        try:
            self.server.accounts().account_id(account_id).call()
            return True
        except NotFoundError:
            return False

    def get_balance(self, account_id: str) -> Dict[str, str]:
        """
        Get the XLM balance and other assets for an account.

        Args:
            account_id: Public key of the account

        Returns:
            Dictionary with balance information
            Example: {'native': '100.0000000', 'assets': []}

        Raises:
            PaymentError: If account does not exist
        """
        try:
            account_data = self.server.accounts().account_id(account_id).call()
            balances = {'native': '0', 'assets': []}

            for balance in account_data['balances']:
                if balance['asset_type'] == 'native':
                    balances['native'] = balance['balance']
                else:
                    balances['assets'].append({
                        'asset_code': balance.get('asset_code', ''),
                        'asset_issuer': balance.get('asset_issuer', ''),
                        'balance': balance['balance']
                    })

            return balances
        except NotFoundError:
            raise PaymentError(f"Account {account_id} does not exist on the network.")

    def get_transaction_history(self, account_id: str, limit: int = 10) -> list:
        """
        Get recent transaction history for an account.

        Args:
            account_id: Public key of the account
            limit: Maximum number of transactions to return (default: 10)

        Returns:
            List of transaction dictionaries with relevant details

        Raises:
            PaymentError: If account does not exist
        """
        try:
            transactions = (
                self.server.transactions()
                .for_account(account_id)
                .limit(limit)
                .order(desc=True)
                .call()
            )

            result = []
            for tx in transactions['_embedded']['records']:
                result.append({
                    'hash': tx['hash'],
                    'created_at': tx['created_at'],
                    'source_account': tx['source_account'],
                    'fee_charged': tx['fee_charged'],
                    'operation_count': tx['operation_count'],
                    'memo': tx.get('memo', 'None')
                })

            return result
        except NotFoundError:
            raise PaymentError(f"Account {account_id} does not exist on the network.")

    def send_payment(
        self,
        source_secret: str,
        destination_public: str,
        amount: float,
        memo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send XLM payment to a destination address.

        Now includes:
        - Destination existence pre-flight check
        - Precise amount formatting using format_stellar_amount()
        - Optional memo support (max 28 bytes)
        - Comprehensive error handling with PaymentError

        Args:
            source_secret: Secret key of the source account
            destination_public: Public key of the destination account
            amount: Amount of XLM to send
            memo: Optional text memo (max 28 characters)

        Returns:
            Transaction response dictionary

        Raises:
            PaymentError: For all payment-related failures with user-friendly messages
        """
        # Pre-flight check: verify destination exists
        if not self.account_exists(destination_public):
            raise PaymentError(
                f"Destination account {destination_public} does not exist on "
                "the network. The recipient must activate their account by "
                "receiving at least 1 XLM from another funded account first."
            )

        # Format amount to Stellar-safe string (no float precision issues)
        stellar_amount = format_stellar_amount(amount)

        try:
            source_keypair = Keypair.from_secret(source_secret)
            source_account = self.server.load_account(source_keypair.public_key)

            builder = TransactionBuilder(
                source_account=source_account,
                network_passphrase=config.network_passphrase,
                base_fee=100,
            )

            # Add optional memo (enforce Stellar's 28-byte limit)
            if memo:
                memo = memo[:28]
                builder = builder.add_text_memo(memo)

            transaction = (
                builder
                .append_operation(
                    Payment(
                        destination=destination_public,
                        asset=Asset.native(),
                        amount=stellar_amount
                    )
                )
                .set_timeout(30)
                .build()
            )

            transaction.sign(source_keypair)
            response = self.server.submit_transaction(transaction)
            return response

        except NotFoundError:
            raise PaymentError(
                "Source account not found. Please ensure your SOURCE_SECRET "
                "is correct and the account is funded on the network."
            )
        except BadRequestError as e:
            # Parse Horizon error codes for user-friendly messages
            result_codes = e.extras.get("result_codes", {})

            if "op_underfunded" in result_codes.get("operations", []):
                raise PaymentError(
                    f"Insufficient balance. You do not have enough XLM to send "
                    f"{stellar_amount} XLM (remember the 1 XLM minimum reserve)."
                )
            if "op_no_destination" in result_codes.get("operations", []):
                raise PaymentError(
                    f"Destination account {destination_public} is not active."
                )
            if result_codes.get("transaction") == "tx_bad_seq":
                raise PaymentError(
                    "Sequence number mismatch. Please retry the transaction."
                )

            # Generic BadRequestError fallback
            raise PaymentError(
                f"Transaction rejected by network. Details: {result_codes}"
            )
        except Exception as e:
            # Catch-all for unexpected errors (network issues, etc.)
            raise PaymentError(
                f"Unexpected error during payment: {type(e).__name__}"
            )

    def add_signer(
        self,
        source_secret: str,
        signer_public_key: str,
        weight: int = 1
    ) -> Dict[str, Any]:
        """
        Add a signer to an account for multi-signature support.

        Args:
            source_secret: Secret key of the account owner
            signer_public_key: Public key of the signer to add
            weight: Weight of the signer (default: 1)

        Returns:
            Transaction response dictionary

        Raises:
            PaymentError: If operation fails
        """
        try:
            source_keypair = Keypair.from_secret(source_secret)
            source_account = self.server.load_account(source_keypair.public_key)

            transaction = (
                TransactionBuilder(
                    source_account=source_account,
                    network_passphrase=config.network_passphrase,
                    base_fee=100
                )
                .append_operation(
                    SetOptions(
                        signer=Signer.ed25519_public_key(signer_public_key, weight)
                    )
                )
                .set_timeout(30)
                .build()
            )

            transaction.sign(source_keypair)
            response = self.server.submit_transaction(transaction)
            return response

        except NotFoundError:
            raise PaymentError("Source account not found.")
        except BadRequestError as e:
            raise PaymentError(f"Failed to add signer: {e.extras.get('result_codes', {})}")

    def send_payment_multisig(
        self,
        transaction_xdr: str,
        signers: List[str]
    ) -> Dict[str, Any]:
        """
        Submit a multi-signature transaction.

        Args:
            transaction_xdr: Base64-encoded transaction XDR
            signers: List of secret keys to sign the transaction

        Returns:
            Transaction response dictionary

        Raises:
            PaymentError: If transaction submission fails
        """
        try:
            transaction = Transaction.from_xdr(transaction_xdr, config.network_passphrase)

            # Sign with all provided signers
            for signer_secret in signers:
                signer_keypair = Keypair.from_secret(signer_secret)
                transaction.sign(signer_keypair)

            response = self.server.submit_transaction(transaction)
            return response

        except BadRequestError as e:
            result_codes = e.extras.get("result_codes", {})
            if "tx_bad_auth" in str(result_codes):
                raise PaymentError("Insufficient signatures for multi-sig transaction.")
            raise PaymentError(f"Multi-sig transaction failed: {result_codes}")
        except Exception as e:
            raise PaymentError(f"Multi-sig transaction error: {type(e).__name__}")
