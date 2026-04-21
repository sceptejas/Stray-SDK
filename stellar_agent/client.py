"""Stellar blockchain client for payment operations."""
from stellar_sdk import Server, Keypair, TransactionBuilder, Asset
from stellar_sdk.operation import Payment, CreateAccount
from stellar_sdk.exceptions import NotFoundError, BadRequestError
from typing import Dict, Any, Tuple, List, Optional
from decimal import Decimal
from .config import config
from .utils.error_handlers import StellarErrorHandler

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
            error_msg = StellarErrorHandler.handle_stellar_error(
                NotFoundError(), "account information fetch"
            )
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = StellarErrorHandler.handle_stellar_error(e, "account information fetch")
            raise RuntimeError(error_msg)
    
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
                error_msg = StellarErrorHandler.handle_stellar_error(e, "payment transaction")
                raise RuntimeError(error_msg)
            except Exception as e:
                error_msg = StellarErrorHandler.handle_stellar_error(e, "payment transaction")
                raise RuntimeError(error_msg)
                
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Payment operation failed: {e}")
    
    def get_transaction_history(self, account_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get transaction history for an account.
        
        Args:
            account_id: Public key of the account
            limit: Maximum number of transactions to retrieve (default: 10)
            
        Returns:
            List of transaction dictionaries
            
        Raises:
            RuntimeError: If account is not found or network issues occur
        """
        try:
            transactions = self.server.transactions().for_account(account_id).limit(limit).call()
            return transactions.get('_embedded', {}).get('records', [])
        except NotFoundError:
            raise RuntimeError(f"Account {account_id} not found on the Stellar network.")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch transaction history: {e}")
    
    def get_transaction_status(self, transaction_hash: str) -> Dict[str, Any]:
        """
        Get the status and details of a specific transaction.
        
        Args:
            transaction_hash: Hash of the transaction to check
            
        Returns:
            Transaction details dictionary
            
        Raises:
            RuntimeError: If transaction is not found or network issues occur
        """
        try:
            transaction = self.server.transactions().transaction(transaction_hash).call()
            return transaction
        except NotFoundError:
            raise RuntimeError(f"Transaction {transaction_hash} not found on the Stellar network.")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch transaction status: {e}")
    
    def create_account(self, source_secret: str, starting_balance: float) -> Tuple[str, str]:
        """
        Create a new Stellar account and fund it with XLM.
        
        Args:
            source_secret: Secret key of the funding account
            starting_balance: Amount of XLM to send to the new account
            
        Returns:
            Tuple of (new_public_key, new_secret_key)
            
        Raises:
            RuntimeError: If account creation fails
        """
        try:
            # Generate new keypair for the new account
            new_keypair = Keypair.random()
            new_public_key = new_keypair.public_key
            new_secret_key = new_keypair.secret
            
            # Create and fund the new account
            source_keypair = Keypair.from_secret(source_secret)
            source_public_key = source_keypair.public_key
            
            # Load source account
            source_account = self.server.load_account(source_public_key)
            
            # Build transaction to create account
            transaction = (
                TransactionBuilder(
                    source_account=source_account,
                    network_passphrase=config.network_passphrase,
                    base_fee=100,
                )
                .append_operation(
                    CreateAccount(
                        destination=new_public_key,
                        starting_balance=str(starting_balance)
                    )
                )
                .set_timeout(30)
                .build()
            )
            
            # Sign and submit transaction
            transaction.sign(source_keypair)
            response = self.server.submit_transaction(transaction)
            
            return new_public_key, new_secret_key
            
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Account creation failed: {e}")
    
    def get_account_balance_detailed(self, account_id: str) -> Dict[str, Any]:
        """
        Get detailed balance information for an account.
        
        Args:
            account_id: Public key of the account
            
        Returns:
            Dictionary with detailed balance information
            
        Raises:
            RuntimeError: If account is not found or network issues occur
        """
        try:
            account_info = self.get_account_info(account_id)
            balances = []
            
            for balance in account_info.get('balances', []):
                balance_info = {
                    'asset_type': balance.get('asset_type'),
                    'asset_code': balance.get('asset_code', 'XLM'),
                    'balance': balance.get('balance'),
                    'limit': balance.get('limit'),
                    'buying_liabilities': balance.get('buying_liabilities', '0.0000000'),
                    'selling_liabilities': balance.get('selling_liabilities', '0.0000000')
                }
                
                # Calculate available balance
                total = Decimal(balance.get('balance', '0'))
                buying_liabilities = Decimal(balance.get('buying_liabilities', '0'))
                selling_liabilities = Decimal(balance.get('selling_liabilities', '0'))
                balance_info['available'] = str(total - buying_liabilities - selling_liabilities)
                
                balances.append(balance_info)
            
            return {
                'account_id': account_id,
                'balances': balances,
                'sequence': account_info.get('sequence'),
                'num_subentries': account_info.get('num_subentries', 0),
                'thresholds': account_info.get('thresholds', {}),
                'flags': account_info.get('flags', {})
            }
            
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Failed to get detailed balance: {e}")
