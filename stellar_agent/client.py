"""Stellar blockchain client for payment operations."""

from decimal import Decimal
from typing import Any, Dict, Tuple

from stellar_sdk import Asset, Keypair, Server, TransactionBuilder
from stellar_sdk.exceptions import BadRequestError, NotFoundError
from stellar_sdk.operation import Payment

from .config import config


class StellarClient:
    """Client for interacting with the Stellar blockchain."""

    def __init__(self):
        self.server = Server(config.horizon_url)

    def get_account_info(self, account_id: str) -> Dict[str, Any]:
        try:
            return self.server.accounts().account_id(account_id).call()
        except NotFoundError as exc:
            raise RuntimeError(
                f"Account {account_id} not found on the Stellar network. "
                "Check that the account is funded and the network URL is correct."
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Failed to fetch account information: {exc}. "
                "Check your network connectivity and Horizon URL configuration."
            ) from exc

    def get_account_balance(self, account_id: str) -> Tuple[Decimal, bool]:
        try:
            account_info = self.get_account_info(account_id)

            for balance in account_info.get("balances", []):
                if balance.get("asset_type") == "native":
                    return Decimal(balance["balance"]), True

            return Decimal("0"), True
        except RuntimeError:
            return Decimal("0"), False

    def check_sufficient_balance(
        self, source_account_id: str, amount: float
    ) -> Tuple[bool, Decimal, str]:
        balance, account_exists = self.get_account_balance(source_account_id)

        if not account_exists:
            return False, balance, "Source account not found or not funded"

        payment_amount = Decimal(str(amount))
        estimated_fee = Decimal("0.00001")
        minimum_balance_value = getattr(config, "minimum_balance_xlm", Decimal("1"))
        minimum_reserve = (
            minimum_balance_value
            if isinstance(minimum_balance_value, Decimal)
            else Decimal(str(minimum_balance_value))
        )
        total_required = payment_amount + estimated_fee + minimum_reserve

        if balance < total_required:
            return False, balance, (
                f"Insufficient balance. Required: {total_required} XLM "
                f"(Payment: {payment_amount}, Fee: {estimated_fee}, Reserve: {minimum_reserve}), "
                f"Available: {balance} XLM"
            )

        return True, balance, ""

    def send_payment(
        self,
        source_secret: str,
        destination_public: str,
        amount: float,
    ) -> Dict[str, Any]:
        try:
            source_keypair = Keypair.from_secret(source_secret)
            source_public_key = source_keypair.public_key

            if getattr(config, "balance_check_enabled", False) is True:
                sufficient, _, error_msg = self.check_sufficient_balance(
                    source_public_key, amount
                )
                if not sufficient:
                    raise RuntimeError(f"Balance check failed: {error_msg}")

            try:
                source_account = self.server.load_account(source_public_key)
            except NotFoundError as exc:
                raise RuntimeError(
                    f"Source account {source_public_key} not found. "
                    "Ensure the account is funded and you're connected to the correct network."
                ) from exc
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to load source account: {exc}. "
                    "Check network connectivity and Horizon URL."
                ) from exc

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
                        amount=str(amount),
                    )
                )
                .set_timeout(30)
                .build()
            )

            transaction.sign(source_keypair)

            try:
                return self.server.submit_transaction(transaction)
            except BadRequestError as exc:
                error_detail = str(exc)

                if "insufficient balance" in error_detail.lower():
                    raise RuntimeError(
                        "Transaction failed: Insufficient balance for payment and fees."
                    ) from exc
                if "destination account does not exist" in error_detail.lower():
                    raise RuntimeError(
                        "Transaction failed: Destination account does not exist."
                    ) from exc

                raise RuntimeError(f"Transaction failed: {error_detail}") from exc
            except Exception as exc:
                raise RuntimeError(
                    f"Transaction submission failed: {exc}. "
                    "Check network connectivity and try again."
                ) from exc

        except Exception as exc:
            if isinstance(exc, RuntimeError):
                raise
            raise RuntimeError(f"Payment operation failed: {exc}") from exc
