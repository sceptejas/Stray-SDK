"""Input validation utilities."""
import re
from typing import Tuple

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

def validate_stellar_address(address: str) -> Tuple[bool, str]:
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
    
    # Check length
    if len(address) != 56:
        return False, f"Invalid address length: {len(address)} characters. Stellar addresses must be exactly 56 characters long."
    
    # Check starting character
    if not address.startswith('G'):
        return False, f"Invalid address prefix: '{address[0] if address else 'empty'}'. Stellar addresses must start with 'G'."
    
    # Check character set (Stellar uses Base32: A-Z and 2-7)
    pattern = r'^G[A-Z2-7]{55}$'
    if not re.match(pattern, address):
        # Find invalid characters for better error message
        invalid_chars = []
        for char in address[1:]:  # Skip the 'G' prefix
            if not (char.isupper() and char.isalpha()) and char not in '234567':
                invalid_chars.append(char)
        
        if invalid_chars:
            return False, f"Invalid characters found: {', '.join(set(invalid_chars))}. Stellar addresses only use uppercase letters A-Z and numbers 2-7."
        else:
            return False, "Invalid address format. Stellar addresses must start with 'G' followed by 55 characters from A-Z and 2-7."
    
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
