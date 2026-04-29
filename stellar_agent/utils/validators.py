"""Input validation utilities."""
import re

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

def is_valid_asset_code(asset_code: str) -> bool:
    """
    Validate Stellar asset code format.
    
    Args:
        asset_code: Asset code to validate (1-12 alphanumeric characters)
        
    Returns:
        True if valid, False otherwise
    """
    if not asset_code:
        return False
    
    # Asset codes are 1-12 alphanumeric characters
    pattern = r'^[a-zA-Z0-9]{1,12}$'
    return bool(re.match(pattern, asset_code))
