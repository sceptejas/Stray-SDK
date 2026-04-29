"""Stellar blockchain client for payment operations."""
from stellar_sdk import Server, Keypair, TransactionBuilder, Asset
from stellar_sdk.operation import Payment
from stellar_sdk.exceptions import NotFoundError, BadRequestError
from typing import Dict, Any, Tuple
from decimal import Decimal
from .config import config
from .utils.validators import validate_transaction_inputs, validate_stellar_address

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
    
    def check_sufficient_balance(self, source_account_id: str, amount: float) -> Tuple[bool, Decimal, str]:
        """
        Check if account has sufficient balance for payment + fees + minimum balance.
        
        Args:
            source_account_id: Public key of the source account
            amount: Amount to send in XLM
            
        Returns:
            Tuple of (is_sufficient, current_balance, error_message)
        """
        balance, account_exists = self.get_account_balance(source_account_id)
        
        if not account_exists:
            return False, balance, "Source account not found or not funded"
        
        # Calculate total cost: payment + estimated fee + minimum balance reserve
        payment_amount = Decimal(str(amount))
        estimated_fee = Decimal('0.00001')  # Base fee
        minimum_reserve = Decimal(str(config.minimum_balance_xlm))
        
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
            RuntimeError: If validation fails, balance is insufficient, network issues, or transaction fails
        """
        # Validate all inputs before attempting any operations
        is_valid, error_msg = validate_transaction_inputs(source_secret, destination_public, amount)
        if not is_valid:
            raise RuntimeError(f"Validation failed: {error_msg}")
        
        try:
            source_keypair = Keypair.from_secret(source_secret)
            source_public_key = source_keypair.public_key
            
            # Balance check if enabled
            if config.balance_check_enabled:
                sufficient, balance, error_msg = self.check_sufficient_balance(source_public_key, amount)
                if not sufficient:
                    raise RuntimeError(f"Balance check failed: {error_msg} 💡 Please fund your account with additional XLM or reduce the payment amount.")
            
            # Load source account
            try:
                source_account = self.server.load_account(source_public_key)
            except NotFoundError:
                raise RuntimeError(
                    f"Source account {source_public_key} not found on the Stellar network. "
                    f"💡 Possible solutions:\n"
                    f"   1. Fund the account with at least 1 XLM to create it\n"
                    f"   2. Check if you're connected to the correct network (testnet/mainnet)\n"
                    f"   3. Verify your secret key corresponds to an existing account"
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load source account: {e}. "
                    f"💡 Please check:\n"
                    f"   1. Network connectivity to Horizon server\n"
                    f"   2. Horizon URL configuration\n"
                    f"   3. Account status on Stellar network"
                )

            # Validate destination account exists before building transaction
            try:
                dest_is_valid, dest_error = validate_stellar_address(destination_public)
                if not dest_is_valid:
                    raise RuntimeError(f"Destination address validation failed: {dest_error}")
                
                # Check if destination account exists
                self.get_account_info(destination_public)
            except RuntimeError as e:
                if "not found" in str(e).lower():
                    raise RuntimeError(
                        f"Destination account {destination_public} does not exist. "
                        f"💡 The recipient must have an active Stellar account to receive payments. "
                        f"Ask them to fund their account first, or send at least 1 XLM to create it."
                    )
                else:
                    raise RuntimeError(f"Destination validation failed: {e}")

            # Build transaction
            try:
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
            except Exception as e:
                raise RuntimeError(
                    f"Failed to build transaction: {e}. "
                    f"💡 Please check transaction parameters and try again."
                )

            # Sign and submit transaction
            try:
                transaction.sign(source_keypair)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to sign transaction: {e}. "
                    f"💡 Please verify your secret key is correct and try again."
                )
            
            try:
                response = self.server.submit_transaction(transaction)
                return response
            except BadRequestError as e:
                # Parse common Stellar errors with enhanced messages
                error_detail = str(e).lower()
                if "insufficient balance" in error_detail:
                    raise RuntimeError(
                        "Transaction failed: Insufficient balance for payment and fees. "
                        f"💡 Your account needs at least {amount + 0.00001 + config.minimum_balance_xlm} XLM. "
                        f"Current balance is too low to cover the payment, transaction fee (0.00001 XLM), and minimum reserve ({config.minimum_balance_xlm} XLM)."
                    )
                elif "destination account does not exist" in error_detail:
                    raise RuntimeError(
                        "Transaction failed: Destination account does not exist. "
                        f"💡 The recipient must have an active Stellar account. "
                        f"Send at least 1 XLM to create their account first."
                    )
                elif "transaction malformed" in error_detail or "invalid transaction" in error_detail:
                    raise RuntimeError(
                        "Transaction failed: Invalid transaction format. "
                        f"💡 This could be due to sequence number issues or network problems. "
                        f"Please try again in a few moments."
                    )
                elif "operation failed" in error_detail:
                    raise RuntimeError(
                        "Transaction failed: Operation could not be executed. "
                        f"💡 This might be due to temporary network issues or account restrictions. "
                        f"Please try again or check account settings."
                    )
                else:
                    raise RuntimeError(
                        f"Transaction failed: {e}. "
                        f"💡 Check transaction parameters, network connectivity, and try again. "
                        f"If the problem persists, the network might be experiencing high load."
                    )
            except Exception as e:
                raise RuntimeError(
                    f"Transaction submission failed: {e}. "
                    f"💡 Please check:\n"
                    f"   1. Network connectivity to Stellar network\n"
                    f"   2. Horizon server status\n"
                    f"   3. Transaction was not double-signed\n"
                    f"   4. Try again in a few moments"
                )
                
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(
                f"Payment operation failed: {e}. "
                f"💡 Please verify all inputs and try again. "
                f"If issues persist, check Stellar network status."
            )
