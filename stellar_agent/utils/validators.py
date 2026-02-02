"""Input validation utilities."""
import re
from stellar_sdk import Keypair
from stellar_sdk.exceptions import MuxedEd25519AccountInvalidError, Ed25519SecretSeedInvalidError

def is_valid_stellar_address(address: str) -> bool:
    """
    Validate Stellar public key using cryptographic validation.
    
    Uses stellar-sdk's Keypair.from_public_key() for proper validation
    instead of just regex pattern matching.
    
    Args:
        address: Public key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not address:
        return False
    
    # First check basic format (optimization to avoid expensive validation)
    if not re.match(r'^G[A-Z2-7]{55}$', address):
        return False
    
    # Use stellar-sdk's cryptographic validation
    try:
        Keypair.from_public_key(address)
        return True
    except (MuxedEd25519AccountInvalidError, Ed25519SecretSeedInvalidError, ValueError):
        return False

def is_valid_amount(amount: float) -> bool:
    """
    Validate payment amount.
    
    Args:
        amount: Amount to validate
        
    Returns:
        True if valid, False otherwise
    """
    return amount > 0
