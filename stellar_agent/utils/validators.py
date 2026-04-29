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
    is_valid, _ = validate_stellar_address(address)
    return is_valid

def validate_stellar_address(address: str) -> tuple[bool, str]:
    """
    Validate Stellar public key format with detailed error messages.
    
    Args:
        address: Public key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not address:
        return False, "Address cannot be empty"
    
    if not isinstance(address, str):
        return False, "Address must be a string"
    
    # Remove whitespace and check if empty after trimming
    trimmed_address = address.strip()
    if not trimmed_address:
        return False, "Address cannot be empty or whitespace only"
    
    if trimmed_address != address:
        return False, "Address cannot contain leading or trailing whitespace"
    
    # Check length
    if len(address) != 56:
        return False, f"Invalid address length: {len(address)} characters. Stellar addresses must be exactly 56 characters long"
    
    # Check prefix
    if not address.startswith('G'):
        if address.startswith('S'):
            return False, "Invalid address format: This appears to be a secret key (starts with 'S'). Public keys must start with 'G'"
        elif len(address) == 56 and address[0].isalpha():
            return False, f"Invalid address prefix: '{address[0]}'. Stellar public keys must start with 'G'"
        else:
            return False, f"Invalid address format: Stellar public keys must start with 'G'"
    
    # Check character set (Stellar uses base32 with A-Z and 2-7)
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567')
    invalid_chars = set(address[1:]) - valid_chars  # Skip the 'G' prefix
    
    if invalid_chars:
        invalid_list = sorted(list(invalid_chars))
        return False, f"Invalid characters in address: {', '.join(invalid_list)}. Stellar addresses only use letters A-Z and numbers 2-7"
    
    # If all checks pass
    return True, ""

def is_valid_amount(amount: float) -> bool:
    """
    Validate payment amount.
    
    Args:
        amount: Amount to validate
        
    Returns:
        True if valid, False otherwise
    """
    return amount > 0
