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

def is_valid_secret_key(secret: str) -> bool:
    """
    Validate Stellar secret key format.
    
    Args:
        secret: Secret key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not secret:
        return False
    
    # Stellar secret keys start with 'S' and are 56 characters long
    pattern = r'^S[A-Z2-7]{55}$'
    return bool(re.match(pattern, secret))

def is_valid_weight(weight: int) -> bool:
    """
    Validate signer weight.
    
    Args:
        weight: Weight to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 1 <= weight <= 255

def is_valid_threshold(threshold: int) -> bool:
    """
    Validate signature threshold.
    
    Args:
        threshold: Threshold to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 1 <= threshold <= 255

def validate_signer_configuration(signers: list, threshold: int) -> tuple[bool, str]:
    """
    Validate multi-signature signer configuration.
    
    Args:
        signers: List of signer dictionaries
        threshold: Signature threshold
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not signers:
        return False, "At least one signer is required"
    
    if len(signers) > 20:
        return False, "Maximum 20 signers allowed"
    
    total_weight = 0
    for signer in signers:
        if not is_valid_stellar_address(signer.get('public_key', '')):
            return False, f"Invalid signer address: {signer.get('public_key', '')}"
        
        weight = signer.get('weight', 0)
        if not is_valid_weight(weight):
            return False, f"Invalid weight for signer {signer.get('public_key', '')}: {weight}"
        
        total_weight += weight
    
    if total_weight < threshold:
        return False, f"Total signer weight ({total_weight}) is less than threshold ({threshold})"
    
    return True, ""
