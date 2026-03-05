"""Input validation utilities."""
import re
from typing import Optional
from stellar_sdk import Keypair, TransactionEnvelope
from stellar_sdk.exceptions import SdkError

def is_valid_stellar_address(address: str) -> bool:
    """
    Validate Stellar public key format.
    
    Args:
        address: Public key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not address:
        return False
    
    # Stellar public keys start with 'G' and are 56 characters long
    pattern = r'^G[A-Z2-7]{55}$'
    return bool(re.match(pattern, address))

def is_valid_amount(amount: float) -> bool:
    """
    Validate payment amount.
    
    Args:
        amount: Amount to validate
        
    Returns:
        True if valid, False otherwise
    """
    return amount > 0


def is_valid_secret_key(secret_key: str) -> bool:
    """
    Validate Stellar secret key format.
    
    Args:
        secret_key: Secret key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not secret_key:
        return False
    
    try:
        # Stellar secret keys start with 'S' and are 56 characters long
        pattern = r'^S[A-Z2-7]{55}$'
        if not bool(re.match(pattern, secret_key)):
            return False
        
        # Verify it can create a valid keypair
        Keypair.from_secret(secret_key)
        return True
    except (SdkError, ValueError, Exception):
        return False


def is_valid_xdr(xdr_string: str) -> bool:
    """
    Validate XDR transaction envelope format.
    
    Args:
        xdr_string: XDR string to validate
        
    Returns:
        True if valid transaction XDR, False otherwise
    """
    if not xdr_string or not isinstance(xdr_string, str):
        return False
    
    try:
        # Try to parse the XDR as a TransactionEnvelope
        TransactionEnvelope.from_xdr(xdr_string)
        return True
    except (SdkError, ValueError, Exception):
        return False


def get_public_key_from_secret(secret_key: str) -> Optional[str]:
    """
    Extract public key from secret key.
    
    Args:
        secret_key: Valid Stellar secret key
        
    Returns:
        Public key if successful, None otherwise
    """
    try:
        keypair = Keypair.from_secret(secret_key)
        return keypair.public_key
    except (SdkError, ValueError, Exception):
        return None
