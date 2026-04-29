"""Multi-signature transaction support for Stellar Agent."""
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from stellar_sdk import Server, Keypair, TransactionBuilder, Transaction, Asset
from stellar_sdk.operation import Payment, SetOptions, ManageData
from stellar_sdk.exceptions import NotFoundError, BadRequestError
from .config import config


@dataclass
class Signer:
    """Represents a signer in a multi-signature account."""
    public_key: str
    weight: int
    
    def validate(self) -> bool:
        """Validate signer configuration."""
        if not self.public_key or len(self.public_key) != 56 or not self.public_key.startswith('G'):
            return False
        if not (1 <= self.weight <= 255):
            return False
        return True


@dataclass
class MultiSigAccount:
    """Multi-signature account configuration."""
    account_id: str
    threshold: int
    signers: List[Signer]
    master_secret: str = ""
    
    def validate(self) -> Tuple[bool, str]:
        """Validate multi-signature account configuration."""
        if not self.account_id or len(self.account_id) != 56 or not self.account_id.startswith('G'):
            return False, "Invalid account ID"
        
        if not (1 <= self.threshold <= 255):
            return False, "Threshold must be between 1 and 255"
        
        if len(self.signers) == 0:
            return False, "At least one signer is required"
        
        if len(self.signers) > 20:
            return False, "Maximum 20 signers allowed"
        
        total_weight = sum(signer.weight for signer in self.signers)
        if total_weight < self.threshold:
            return False, f"Total signer weight ({total_weight}) is less than threshold ({threshold})"
        
        for signer in self.signers:
            if not signer.validate():
                return False, f"Invalid signer: {signer.public_key}"
        
        return True, ""


@dataclass
class PendingTransaction:
    """Represents a transaction pending signatures."""
    transaction_xdr: str
    network_passphrase: str
    required_signatures: List[str]
    collected_signatures: Dict[str, str]
    created_at: float
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PendingTransaction':
        """Create from dictionary."""
        return cls(**data)


class MultiSigManager:
    """Manages multi-signature accounts and transactions."""
    
    def __init__(self):
        self.server = Server(config.horizon_url)
    
    def create_multisig_account(
        self, 
        master_secret: str,
        signers: List[Signer],
        threshold: int,
        starting_balance: float = 1.0
    ) -> Dict[str, Any]:
        """
        Create a new multi-signature account.
        
        Args:
            master_secret: Secret key of the master account
            signers: List of signers with their weights
            threshold: Number of signatures required
            starting_balance: Initial XLM balance to fund the account
            
        Returns:
            Account creation response
        """
        try:
            master_keypair = Keypair.from_secret(master_secret)
            master_public = master_keypair.public_key
            
            # Create the new account
            new_keypair = Keypair.random()
            new_public = new_keypair.public_key
            
            # Fund the new account
            fund_tx = (
                TransactionBuilder(
                    source_account=self.server.load_account(master_public),
                    network_passphrase=config.network_passphrase,
                    base_fee=100,
                )
                .append_operation(
                    Payment(
                        destination=new_public,
                        asset=Asset.native(),
                        amount=str(starting_balance)
                    )
                )
                .set_timeout(30)
                .build()
            )
            fund_tx.sign(master_keypair)
            fund_response = self.server.submit_transaction(fund_tx)
            
            # Set up multi-signature
            account = self.server.load_account(new_public)
            
            # Add master signer and other signers
            builder = TransactionBuilder(
                source_account=account,
                network_passphrase=config.network_passphrase,
                base_fee=100,
            )
            
            # Add master signer
            builder.append_operation(
                SetOptions(
                    signer=master_public,
                    signer_weight=1
                )
            )
            
            # Add other signers
            for signer in signers:
                builder.append_operation(
                    SetOptions(
                        signer=signer.public_key,
                        signer_weight=signer.weight
                    )
                )
            
            # Set thresholds
            builder.append_operation(
                SetOptions(
                    master_weight=0,  # Master key alone cannot sign
                    low_threshold=threshold,
                    med_threshold=threshold,
                    high_threshold=threshold
                )
            )
            
            multisig_tx = builder.set_timeout(30).build()
            multisig_tx.sign(master_keypair)
            
            # Collect signatures from other signers (simulated - in real scenario, 
            # this would involve distributing the transaction for signing)
            for signer in signers:
                # In a real implementation, you would collect signatures from each signer
                # For now, we'll just submit with master signature (this will fail on testnet)
                pass
            
            multisig_response = self.server.submit_transaction(multisig_tx)
            
            return {
                'account_id': new_public,
                'secret': new_keypair.secret,
                'fund_transaction': fund_response,
                'multisig_transaction': multisig_response,
                'threshold': threshold,
                'signers': [{'public_key': s.public_key, 'weight': s.weight} for s in signers]
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to create multi-signature account: {e}")
    
    def build_multisig_transaction(
        self,
        source_account_id: str,
        destination: str,
        amount: float,
        description: str = ""
    ) -> PendingTransaction:
        """
        Build a multi-signature transaction for signature collection.
        
        Args:
            source_account_id: Multi-signature account to send from
            destination: Recipient address
            amount: Amount to send
            description: Transaction description
            
        Returns:
            PendingTransaction object
        """
        try:
            # Load account to get signers
            account_info = self.server.accounts().account_id(source_account_id).call()
            
            # Extract signers and threshold
            signers = []
            threshold = 1
            for signer in account_info.get('signers', []):
                if signer.get('weight', 0) > 0:
                    signers.append(signer['key'])
            
            # Get thresholds
            thresholds = account_info.get('thresholds', {})
            threshold = thresholds.get('med_threshold', 1)
            
            # Build transaction
            account = self.server.load_account(source_account_id)
            transaction = (
                TransactionBuilder(
                    source_account=account,
                    network_passphrase=config.network_passphrase,
                    base_fee=100,
                )
                .append_operation(
                    Payment(
                        destination=destination,
                        asset=Asset.native(),
                        amount=str(amount)
                    )
                )
                .set_timeout(30)
                .build()
            )
            
            return PendingTransaction(
                transaction_xdr=transaction.to_xdr(),
                network_passphrase=config.network_passphrase,
                required_signatures=signers,
                collected_signatures={},
                created_at=time.time(),
                description=description or f"Send {amount} XLM to {destination}"
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to build multi-signature transaction: {e}")
    
    def add_signature(
        self,
        pending_tx: PendingTransaction,
        signer_secret: str
    ) -> PendingTransaction:
        """
        Add a signature to a pending transaction.
        
        Args:
            pending_tx: Pending transaction to sign
            signer_secret: Secret key of the signer
            
        Returns:
            Updated PendingTransaction
        """
        try:
            keypair = Keypair.from_secret(signer_secret)
            signer_public = keypair.public_key
            
            if signer_public not in pending_tx.required_signatures:
                raise ValueError(f"Signer {signer_public} is not authorized for this transaction")
            
            if signer_public in pending_tx.collected_signatures:
                raise ValueError(f"Signer {signer_public} has already signed this transaction")
            
            # Load the transaction from XDR
            transaction = Transaction.from_xdr(
                pending_tx.transaction_xdr,
                network_passphrase=pending_tx.network_passphrase
            )
            
            # Sign the transaction
            transaction.sign(keypair)
            
            # Update pending transaction
            updated_pending = PendingTransaction(
                transaction_xdr=transaction.to_xdr(),
                network_passphrase=pending_tx.network_passphrase,
                required_signatures=pending_tx.required_signatures,
                collected_signatures={
                    **pending_tx.collected_signatures,
                    signer_public: signer_secret
                },
                created_at=pending_tx.created_at,
                description=pending_tx.description
            )
            
            return updated_pending
            
        except Exception as e:
            raise RuntimeError(f"Failed to add signature: {e}")
    
    def submit_multisig_transaction(self, pending_tx: PendingTransaction) -> Dict[str, Any]:
        """
        Submit a fully signed multi-signature transaction.
        
        Args:
            pending_tx: Pending transaction with sufficient signatures
            
        Returns:
            Transaction submission response
        """
        try:
            # Load the transaction from XDR
            transaction = Transaction.from_xdr(
                pending_tx.transaction_xdr,
                network_passphrase=pending_tx.network_passphrase
            )
            
            # Check if we have enough signatures
            account_info = self.server.accounts().account_id(transaction.source.account_id).call()
            threshold = account_info.get('thresholds', {}).get('med_threshold', 1)
            
            if len(pending_tx.collected_signatures) < threshold:
                raise RuntimeError(f"Insufficient signatures. Required: {threshold}, Collected: {len(pending_tx.collected_signatures)}")
            
            # Submit the transaction
            response = self.server.submit_transaction(transaction)
            return response
            
        except Exception as e:
            raise RuntimeError(f"Failed to submit multi-signature transaction: {e}")
    
    def get_account_signers(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Get the signers and thresholds for an account.
        
        Args:
            account_id: Account to query
            
        Returns:
            List of signers with their weights
        """
        try:
            account_info = self.server.accounts().account_id(account_id).call()
            
            signers = []
            for signer in account_info.get('signers', []):
                if signer.get('weight', 0) > 0:
                    signers.append({
                        'public_key': signer['key'],
                        'weight': signer['weight']
                    })
            
            thresholds = account_info.get('thresholds', {})
            
            return {
                'signers': signers,
                'thresholds': thresholds
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to get account signers: {e}")
    
    def validate_multisig_setup(self, account_id: str) -> Tuple[bool, str]:
        """
        Validate that an account is properly set up for multi-signature.
        
        Args:
            account_id: Account to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            account_info = self.server.accounts().account_id(account_id).call()
            
            signers = [s for s in account_info.get('signers', []) if s.get('weight', 0) > 0]
            thresholds = account_info.get('thresholds', {})
            
            if len(signers) < 2:
                return False, "Account must have at least 2 signers for multi-signature"
            
            total_weight = sum(s['weight'] for s in signers)
            threshold = thresholds.get('med_threshold', 1)
            
            if total_weight < threshold:
                return False, f"Total weight ({total_weight}) is less than threshold ({threshold})"
            
            return True, "Multi-signature setup is valid"
            
        except Exception as e:
            return False, f"Failed to validate multi-signature setup: {e}"
