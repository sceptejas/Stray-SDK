"""Stellar blockchain client for payment operations."""
from stellar_sdk import Server, Keypair, TransactionBuilder, Asset
from stellar_sdk.operation import Payment
from stellar_sdk.exceptions import NotFoundError, BadRequestError
from typing import Dict, Any, Tuple
from decimal import Decimal
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
            
        Raises:
            RuntimeError: If account is not found or network issues occur
        """
        try:
            response = self.server.accounts().account_id(account_id).call()
            return response
        except NotFoundError:
            raise RuntimeError(f"Account {account_id} not found on the Stellar network. Check that the account is funded and the network URL is correct.")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch account information: {e}. Check your network connectivity and Horizon URL configuration.")
    
    def get_account_balance(self, account_id: str) -> Tuple[Decimal, bool]:
        """
        Get the XLM balance of an account.
        
        Args:
            account_id: Public key of the account
            
        Returns:
            Tuple of (balance_in_xlm, account_exists)
        """
        try:
            account_info = self.get_account_info(account_id)
            # Find XLM balance
            for balance in account_info.get('balances', []):
                if balance.get('asset_type') == 'native':
                    return Decimal(balance['balance']), True
            return Decimal('0'), True
        except RuntimeError:
            return Decimal('0'), False
    
    # Stellar protocol base reserve per sub-entry. Two base reserves are
    # required for the account itself, plus one per sub-entry (trustlines,
    # offers, signers, data entries, etc.). See:
    # https://developers.stellar.org/docs/learn/fundamentals/lumens#minimum-balance
    _BASE_RESERVE_XLM = Decimal('0.5')

    def _compute_protocol_reserve(self, account_info: Dict[str, Any]) -> Decimal:
        """Return the protocol-required minimum XLM balance for an account.

        ``(2 + subentry_count) * base_reserve``. Falls back to the configured
        ``minimum_balance_xlm`` when ``subentry_count`` is missing from the
        Horizon payload.
        """
        subentry_count = account_info.get('subentry_count')
        if subentry_count is None:
            return Decimal(str(config.minimum_balance_xlm))
        return (Decimal(2) + Decimal(int(subentry_count))) * self._BASE_RESERVE_XLM

    def _native_balance_entry(self, account_info: Dict[str, Any]) -> Dict[str, Any]:
        """Return the native (XLM) balance entry, or an empty dict if absent."""
        for balance in account_info.get('balances', []):
            if balance.get('asset_type') == 'native':
                return balance
        return {}

    def get_spendable_balance(self, account_id: str) -> Tuple[Decimal, bool]:
        """Return the XLM balance the account can actually spend right now.

        Spendable balance = total native balance
                          − native ``selling_liabilities`` (XLM locked in
                            active sell offers on the DEX)
                          − protocol-required minimum reserve
                            (``(2 + subentry_count) * 0.5 XLM``)

        Returns ``(spendable, account_exists)``. ``spendable`` may be
        negative if the account is already below the reserve; callers should
        treat that as zero available funds.
        """
        try:
            account_info = self.get_account_info(account_id)
        except RuntimeError:
            return Decimal('0'), False

        native = self._native_balance_entry(account_info)
        total = Decimal(native.get('balance', '0'))
        selling = Decimal(native.get('selling_liabilities', '0') or '0')
        reserve = self._compute_protocol_reserve(account_info)

        return total - selling - reserve, True

    def check_sufficient_balance(self, source_account_id: str, amount: float) -> Tuple[bool, Decimal, str]:
        """
        Check whether an account can actually send ``amount`` XLM right now.

        Unlike a naive ``balance >= amount`` check, this accounts for:
          * ``selling_liabilities`` — XLM already pledged to open sell offers
            on the Stellar DEX, which cannot be spent until those offers are
            cancelled or filled.
          * The protocol-required minimum reserve, computed dynamically from
            the account's ``subentry_count`` (trustlines, offers, signers,
            data entries). The static ``config.minimum_balance_xlm`` is used
            only as a fallback when Horizon does not return a subentry count.

        Args:
            source_account_id: Public key of the source account.
            amount: Amount to send, in XLM.

        Returns:
            ``(is_sufficient, total_balance, error_message)``. ``total_balance``
            is the raw native XLM balance (unchanged from previous versions for
            backwards compatibility).
        """
        try:
            account_info = self.get_account_info(source_account_id)
        except RuntimeError:
            return False, Decimal('0'), "Source account not found or not funded"

        native = self._native_balance_entry(account_info)
        total_balance = Decimal(native.get('balance', '0'))
        selling_liabilities = Decimal(native.get('selling_liabilities', '0') or '0')
        protocol_reserve = self._compute_protocol_reserve(account_info)

        payment_amount = Decimal(str(amount))
        estimated_fee = Decimal('0.00001')  # Base fee (100 stroops)

        # XLM the account may actually spend right now.
        spendable = total_balance - selling_liabilities - protocol_reserve
        required_to_spend = payment_amount + estimated_fee

        if spendable < required_to_spend:
            parts = [
                f"Payment: {payment_amount}",
                f"Fee: {estimated_fee}",
                f"Reserve: {protocol_reserve}",
            ]
            if selling_liabilities > 0:
                parts.append(f"Selling liabilities: {selling_liabilities}")
            return False, total_balance, (
                f"Insufficient spendable balance. "
                f"Need {required_to_spend} XLM spendable "
                f"({', '.join(parts)}). "
                f"Total: {total_balance} XLM, "
                f"Spendable: {spendable if spendable > 0 else Decimal('0')} XLM"
            )

        return True, total_balance, ""
    
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
            
        Raises:
            RuntimeError: If balance is insufficient, network issues, or transaction fails
        """
        try:
            source_keypair = Keypair.from_secret(source_secret)
            source_public_key = source_keypair.public_key
            
            # Balance check if enabled
            if config.balance_check_enabled:
                sufficient, balance, error_msg = self.check_sufficient_balance(source_public_key, amount)
                if not sufficient:
                    raise RuntimeError(f"Balance check failed: {error_msg}")
            
            # Load source account
            try:
                source_account = self.server.load_account(source_public_key)
            except NotFoundError:
                raise RuntimeError(f"Source account {source_public_key} not found. Ensure the account is funded and you're connected to the correct network.")
            except Exception as e:
                raise RuntimeError(f"Failed to load source account: {e}. Check network connectivity and Horizon URL.")

            # Build transaction
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

            # Sign and submit transaction
            transaction.sign(source_keypair)
            
            try:
                response = self.server.submit_transaction(transaction)
                return response
            except BadRequestError as e:
                # Parse common Stellar errors
                error_detail = str(e)
                if "insufficient balance" in error_detail.lower():
                    raise RuntimeError("Transaction failed: Insufficient balance for payment and fees.")
                elif "destination account does not exist" in error_detail.lower():
                    raise RuntimeError("Transaction failed: Destination account does not exist. The recipient must have an active Stellar account.")
                else:
                    raise RuntimeError(f"Transaction failed: {error_detail}. Check transaction parameters and try again.")
            except Exception as e:
                raise RuntimeError(f"Transaction submission failed: {e}. Check network connectivity and try again.")
                
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Payment operation failed: {e}")
