"""Input validation utilities."""
from decimal import Decimal
from stellar_sdk import Keypair
from stellar_sdk.exceptions import Ed25519PublicKeyInvalidError

def is_valid_stellar_address(address: str) -> bool:
    """
    Validate Stellar public key format using SDK's Ed25519 verification.

    This replaces regex-only validation with cryptographic validation.
    A string like 'GAAAA...AAA' passes regex but is rejected by Horizon.
    Using Keypair.from_public_key() applies the identical check that Horizon uses.

    Args:
        address: Public key to validate

    Returns:
        True if valid Ed25519 public key, False otherwise
    """
    if not address:
        return False

    try:
        Keypair.from_public_key(address)
        return True
    except (Ed25519PublicKeyInvalidError, Exception):
        return False

def is_valid_amount(amount: float) -> bool:
    """
    Validate payment amount against Stellar's rules.

    Stellar enforces:
    - Minimum 1 stroop (0.0000001 XLM)
    - Maximum 7 decimal places

    Args:
        amount: Amount to validate

    Returns:
        True if valid for Stellar network, False otherwise
    """
    if amount <= 0:
        return False

    # Convert to Decimal for exact arithmetic
    d = Decimal(str(amount))

    # Check 7 decimal place limit (Stellar protocol requirement)
    if abs(d.as_tuple().exponent) > 7:
        return False

    # Check minimum stroop (0.0000001 XLM)
    if d < Decimal("0.0000001"):
        return False

    return True

def format_stellar_amount(amount: float) -> str:
    """
    Convert a Python float to a Stellar-safe amount string.

    Python's str(float) produces IEEE-754 artefacts that the Stellar SDK rejects:
        str(0.1 + 0.2) → '0.30000000000000004'
        Payment(..., amount='0.30000000000000004') → ValueError

    This function uses Decimal arithmetic to quantize to 7 decimal places
    and strips trailing zeros.

    Args:
        amount: Numeric amount to format

    Returns:
        String representation safe for Stellar SDK (max 7 decimals)

    Examples:
        >>> format_stellar_amount(0.1 + 0.2)
        '0.3'
        >>> format_stellar_amount(1 / 3)
        '0.3333333'
        >>> format_stellar_amount(10.0)
        '10'
        >>> format_stellar_amount(0.0000001)
        '0.0000001'
    """
    # Convert to Decimal for exact arithmetic
    d = Decimal(str(amount))

    # Quantize to 7 decimal places (Stellar's maximum precision)
    quantized = d.quantize(Decimal('0.0000001'))

    # Format with fixed-point notation to avoid scientific notation
    # Use Python's format() with 'f' to force fixed-point
    result = format(quantized, 'f')

    # Remove trailing zeros after decimal point
    if '.' in result:
        result = result.rstrip('0').rstrip('.')

    return result
