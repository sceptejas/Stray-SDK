"""Input validation utilities."""
import re
from stellar_sdk import Keypair

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

def is_valid_secret_key(secret_key: str) -> bool:
    """
    Validate Stellar secret key format.
    
    Args:
        secret_key: Secret key to validate
        
    Returns:
        True if valid, False otherwise
    """
    is_valid, _ = validate_stellar_secret_key(secret_key)
    return is_valid

def validate_stellar_secret_key(secret_key: str) -> tuple[bool, str]:
    """
    Validate Stellar secret key format with detailed error messages.
    
    Args:
        secret_key: Secret key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not secret_key:
        return False, "Secret key cannot be empty"
    
    if not isinstance(secret_key, str):
        return False, "Secret key must be a string"
    
    # Remove whitespace and check if empty after trimming
    trimmed_secret = secret_key.strip()
    if not trimmed_secret:
        return False, "Secret key cannot be empty or whitespace only"
    
    if trimmed_secret != secret_key:
        return False, "Secret key cannot contain leading or trailing whitespace"
    
    # Check length
    if len(secret_key) != 56:
        return False, f"Invalid secret key length: {len(secret_key)} characters. Stellar secret keys must be exactly 56 characters long"
    
    # Check prefix
    if not secret_key.startswith('S'):
        if secret_key.startswith('G'):
            return False, "Invalid secret key format: This appears to be a public key (starts with 'G'). Secret keys must start with 'S'"
        elif len(secret_key) == 56 and secret_key[0].isalpha():
            return False, f"Invalid secret key prefix: '{secret_key[0]}'. Stellar secret keys must start with 'S'"
        else:
            return False, f"Invalid secret key format: Stellar secret keys must start with 'S'"
    
    # Check character set (Stellar uses base32 with A-Z and 2-7)
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567')
    invalid_chars = set(secret_key[1:]) - valid_chars  # Skip the 'S' prefix
    
    if invalid_chars:
        invalid_list = sorted(list(invalid_chars))
        return False, f"Invalid characters in secret key: {', '.join(invalid_list)}. Stellar secret keys only use letters A-Z and numbers 2-7"
    
    # Try to create a Keypair to validate the secret key format
    try:
        Keypair.from_secret(secret_key)
        return True, ""
    except Exception as e:
        if "invalid secret key" in str(e).lower():
            return False, "Invalid secret key format: The secret key is not a valid Stellar secret key"
        else:
            return False, f"Secret key validation failed: {e}"

def validate_transaction_inputs(source_secret: str, destination_public: str, amount: float) -> tuple[bool, str]:
    """
    Validate all transaction inputs before attempting payment.
    
    Args:
        source_secret: Secret key of the source account
        destination_public: Public key of the destination account
        amount: Amount of XLM to send
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate source secret key
    is_valid, error_msg = validate_stellar_secret_key(source_secret)
    if not is_valid:
        return False, f"Invalid source secret key: {error_msg}"
    
    # Validate destination public key
    is_valid, error_msg = validate_stellar_address(destination_public)
    if not is_valid:
        return False, f"Invalid destination address: {error_msg}"
    
    # Validate amount
    if not is_valid_amount(amount):
        return False, f"Invalid amount: {amount}. Amount must be a positive number greater than 0"
    
    # Check if source and destination are the same
    try:
        source_keypair = Keypair.from_secret(source_secret)
        if source_keypair.public_key == destination_public:
            return False, "Source and destination addresses cannot be the same"
    except Exception:
        return False, "Failed to validate source and destination addresses"
    
    return True, ""
