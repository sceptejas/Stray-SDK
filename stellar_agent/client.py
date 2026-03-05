"""Stellar blockchain client for payment operations."""
from stellar_sdk import Server, Keypair, TransactionBuilder, Asset, TransactionEnvelope
from stellar_sdk.operation import Payment
from typing import Dict, Any, List, Tuple, Optional
from stellar_sdk.exceptions import NotFoundError, BadRequestError
from typing import Dict, Any, Tuple
from decimal import Decimal
from .config import config
from .utils.validators import is_valid_secret_key, get_public_key_from_secret


class MultisigInfo:
    """Data class for multisig account information."""
    
    def __init__(self, required_threshold: int, current_weight: int, signers: List[Dict[str, Any]]):
        self.required_threshold = required_threshold
        self.current_weight = current_weight
        self.signers = signers
        
    @property
    def is_multisig_required(self) -> bool:
        """Check if multiple signatures are required."""
        return self.required_threshold > 1
    
    @property
    def needs_additional_signatures(self) -> bool:
        """Check if additional signatures are needed."""
        return self.current_weight < self.required_threshold


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
    
    def get_multisig_info(self, account_id: str) -> MultisigInfo:
        """
        Get multisig information for an account.
        
        Args:
            account_id: Public key of the account
            
        Returns:
            MultisigInfo object with threshold and signer information
        """
        account_info = self.get_account_info(account_id)
        
        # Get thresholds for different operations
        thresholds = account_info.get('thresholds', {})
        # For payments, we need medium threshold (or high for some operations)
        required_threshold = max(
            thresholds.get('med_threshold', 1),
            thresholds.get('low_threshold', 1)
        )
        
        # Get signers information
        signers = account_info.get('signers', [])
        
        # Calculate current weight (all signers are potentially available)
        total_weight = sum(signer.get('weight', 0) for signer in signers)
        
        return MultisigInfo(
            required_threshold=required_threshold,
            current_weight=total_weight,
            signers=signers
        )
    
    def check_if_multisig_required(self, source_secret: str) -> Tuple[bool, MultisigInfo]:
        """
        Check if the source account requires multisig.
        
        Args:
            source_secret: Source account secret key
            
        Returns:
            Tuple of (is_multisig_required, MultisigInfo)
        """
        source_keypair = Keypair.from_secret(source_secret)
        multisig_info = self.get_multisig_info(source_keypair.public_key)
        
        return multisig_info.is_multisig_required, multisig_info
    
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

        transaction.sign(source_keypair)
        response = self.server.submit_transaction(transaction)
        return response
    
    def build_payment_transaction(
        self,
        source_secret: str,
        destination_public: str,
        amount: float,
        auto_sign: bool = True
    ) -> TransactionEnvelope:
        """
        Build a payment transaction without submitting it.
        
        Args:
            source_secret: Secret key of the source account
            destination_public: Public key of the destination account
            amount: Amount of XLM to send
            auto_sign: Whether to automatically sign with source key
            
        Returns:
            TransactionEnvelope object
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

        if auto_sign:
            transaction.sign(source_keypair)
            
        return transaction
    
    def build_payment_transaction_smart(
        self,
        source_secret: str,
        destination_public: str,
        amount: float
    ) -> Tuple[TransactionEnvelope, MultisigInfo]:
        """
        Build a payment transaction with automatic multisig detection.
        
        Args:
            source_secret: Secret key of the source account
            destination_public: Public key of the destination account
            amount: Amount of XLM to send
            
        Returns:
            Tuple of (TransactionEnvelope, MultisigInfo)
        """
        # Check if multisig is required
        is_multisig, multisig_info = self.check_if_multisig_required(source_secret)
        
        # Build transaction and sign with source key
        transaction = self.build_payment_transaction(
            source_secret, 
            destination_public, 
            amount, 
            auto_sign=True
        )
        
        return transaction, multisig_info
    
    def export_transaction_xdr(self, transaction: TransactionEnvelope) -> str:
        """
        Export transaction as XDR string.
        
        Args:
            transaction: TransactionEnvelope to export
            
        Returns:
            XDR string representation
        """
        return transaction.to_xdr()
    
    def import_transaction_xdr(self, xdr_string: str) -> TransactionEnvelope:
        """
        Import transaction from XDR string.
        
        Args:
            xdr_string: XDR string to import
            
        Returns:
            TransactionEnvelope object
            
        Raises:
            ValueError: If XDR string is invalid
        """
        try:
            return TransactionEnvelope.from_xdr(xdr_string)
        except Exception as e:
            raise ValueError(f"Invalid XDR string: {str(e)}")
    
    def get_transaction_signature_count(self, transaction: TransactionEnvelope) -> int:
        """
        Get the number of signatures currently on a transaction.
        
        Args:
            transaction: TransactionEnvelope to check
            
        Returns:
            Number of signatures
        """
        return len(transaction.signatures)
    
    def get_transaction_info(self, transaction: TransactionEnvelope) -> Dict[str, Any]:
        """
        Get information about a transaction.
        
        Args:
            transaction: TransactionEnvelope to analyze
            
        Returns:
            Dictionary with transaction details
        """
        tx = transaction.transaction
        source_account = tx.source_account_id
        
        # Get multisig info for the source account
        multisig_info = self.get_multisig_info(source_account)
        
        signature_count = self.get_transaction_signature_count(transaction)
        
        return {
            'source_account': source_account,
            'signature_count': signature_count,
            'required_threshold': multisig_info.required_threshold,
            'is_ready_to_submit': signature_count >= multisig_info.required_threshold,
            'needs_more_signatures': signature_count < multisig_info.required_threshold,
            'operations_count': len(tx.operations),
            'sequence_number': tx.sequence,
            'fee': tx.fee
        }
    
    def add_signature_to_transaction(
        self,
        transaction: TransactionEnvelope,
        secret_key: str
    ) -> TransactionEnvelope:
        """
        Add an additional signature to a transaction.
        
        Args:
            transaction: TransactionEnvelope to sign
            secret_key: Secret key to sign with
            
        Returns:
            TransactionEnvelope with additional signature
            
        Raises:
            ValueError: If secret key is invalid
        """
        if not is_valid_secret_key(secret_key):
            raise ValueError("Invalid secret key format")
        
        try:
            signer_keypair = Keypair.from_secret(secret_key)
            transaction.sign(signer_keypair)
            return transaction
        except Exception as e:
            raise ValueError(f"Failed to sign transaction: {str(e)}")
    
    def can_submit_transaction(self, transaction: TransactionEnvelope) -> Tuple[bool, str]:
        """
        Check if a transaction has enough signatures to be submitted.
        
        Args:
            transaction: TransactionEnvelope to check
            
        Returns:
            Tuple of (can_submit, reason)
        """
        tx_info = self.get_transaction_info(transaction)
        
        if tx_info['is_ready_to_submit']:
            return True, "Transaction has sufficient signatures"
        else:
            needed = tx_info['required_threshold'] - tx_info['signature_count']
            return False, f"Need {needed} more signature(s). Current: {tx_info['signature_count']}/{tx_info['required_threshold']}"
    
    def submit_signed_transaction(self, transaction: TransactionEnvelope) -> Dict[str, Any]:
        """
        Submit a fully signed transaction.
        
        Args:
            transaction: TransactionEnvelope to submit
            
        Returns:
            Transaction response dictionary
            
        Raises:
            ValueError: If transaction doesn't have enough signatures
        """
        can_submit, reason = self.can_submit_transaction(transaction)
        if not can_submit:
            raise ValueError(f"Cannot submit transaction: {reason}")
        
        try:
            response = self.server.submit_transaction(transaction)
            return response
        except Exception as e:
            raise ValueError(f"Transaction submission failed: {str(e)}")
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
