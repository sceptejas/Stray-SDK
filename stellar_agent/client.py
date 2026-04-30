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
    
    def get_transaction_history(
        self, 
        account_id: str, 
        limit: int = 10,
        include_failed: bool = False
    ) -> list:
        """
        Fetch transaction history for an account.
        
        Args:
            account_id: Public key of the account
            limit: Maximum number of transactions to fetch (default: 10)
            include_failed: Whether to include failed transactions (default: False)
            
        Returns:
            List of transaction dictionaries with formatted information
            
        Raises:
            RuntimeError: If account is not found or network issues occur
        """
        try:
            # Fetch transactions from Horizon
            transactions_call = (
                self.server.transactions()
                .for_account(account_id)
                .limit(limit)
                .order(desc=True)
                .call()
            )
            
            transactions = []
            for tx in transactions_call.get('_embedded', {}).get('records', []):
                # Skip failed transactions if not requested
                if not include_failed and not tx.get('successful', True):
                    continue
                
                # Parse transaction details
                tx_data = {
                    'hash': tx.get('hash', 'N/A'),
                    'created_at': tx.get('created_at', 'N/A'),
                    'source_account': tx.get('source_account', 'N/A'),
                    'fee_charged': int(tx.get('fee_charged', 0)) / 10000000,  # Convert stroops to XLM
                    'operation_count': tx.get('operation_count', 0),
                    'successful': tx.get('successful', True),
                    'ledger': tx.get('ledger', 'N/A'),
                }
                
                # Fetch operations for this transaction to get payment details
                try:
                    operations = self.server.operations().for_transaction(tx['hash']).call()
                    tx_data['operations'] = []
                    
                    for op in operations.get('_embedded', {}).get('records', []):
                        if op.get('type') == 'payment':
                            op_data = {
                                'type': 'payment',
                                'from': op.get('from', 'N/A'),
                                'to': op.get('to', 'N/A'),
                                'amount': op.get('amount', '0'),
                                'asset_type': op.get('asset_type', 'native'),
                            }
                            tx_data['operations'].append(op_data)
                        elif op.get('type') == 'create_account':
                            op_data = {
                                'type': 'create_account',
                                'account': op.get('account', 'N/A'),
                                'starting_balance': op.get('starting_balance', '0'),
                            }
                            tx_data['operations'].append(op_data)
                        else:
                            op_data = {
                                'type': op.get('type', 'unknown'),
                            }
                            tx_data['operations'].append(op_data)
                except Exception:
                    tx_data['operations'] = []
                
                transactions.append(tx_data)
            
            return transactions
            
        except NotFoundError:
            raise RuntimeError(f"Account {account_id} not found on the Stellar network.")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch transaction history: {e}")
