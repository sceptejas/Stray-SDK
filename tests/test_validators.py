"""Tests for validation utilities."""
import pytest
from stellar_agent.utils.validators import is_valid_stellar_address, is_valid_amount

class TestValidators:
    """Test validation functions."""
    
    def test_valid_stellar_address(self):
        """Test valid Stellar address format with cryptographic validation."""
        # Known valid Stellar public key
        valid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(valid_address) is True
        
        # Another known valid address
        valid_address2 = "GA7QYNF7SOWQ3GLR2BGMZEHXAVIRZA4KVWLTJJFC7MGXUA74P7UJVSGZ"
        assert is_valid_stellar_address(valid_address2) is True
    
    def test_invalid_stellar_address_wrong_prefix(self):
        """Test address with wrong prefix."""
        invalid_address = "ABRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(invalid_address) is False
        
        # Test with other invalid prefixes
        invalid_address2 = "SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H" # S is for secret keys
        assert is_valid_stellar_address(invalid_address2) is False
    
    def test_invalid_stellar_address_wrong_length(self):
        """Test address with wrong length."""
        # Too short
        invalid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX"
        assert is_valid_stellar_address(invalid_address) is False
        
        # Too long
        invalid_address2 = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2HZ"
        assert is_valid_stellar_address(invalid_address2) is False
    
    def test_invalid_stellar_address_bad_characters(self):
        """Test address with invalid characters."""
        # Contains invalid characters (0, 1, 8, 9 not in Base32)
        invalid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX01"
        assert is_valid_stellar_address(invalid_address) is False
        
        # Contains lowercase (should be uppercase)
        invalid_address2 = "gbrpyhil2ci3fnq4bxlfmndlfjunpu2hy3zmfshonuceoasw7qc7ox2h"
        assert is_valid_stellar_address(invalid_address2) is False
    
    def test_invalid_stellar_address_bad_checksum(self):
        """Test address with valid format but invalid checksum (fails crypto validation)."""
        # This has correct format but invalid checksum
        invalid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2Z"
        assert is_valid_stellar_address(invalid_address) is False
    
    def test_empty_address(self):
        """Test empty and None address."""
        assert is_valid_stellar_address("") is False
        assert is_valid_stellar_address(None) is False  # Test with None
    
    def test_whitespace_address(self):
        """Test address with whitespace."""
        # Leading/trailing whitespace should not be accepted
        valid_core = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(f" {valid_core}") is False
        assert is_valid_stellar_address(f"{valid_core} ") is False
        assert is_valid_stellar_address(f" {valid_core} ") is False
    
    def test_valid_amount(self):
        """Test valid payment amounts."""
        assert is_valid_amount(10.5) is True
        assert is_valid_amount(0.0000001) is True  # Minimum XLM amount
        assert is_valid_amount(1000000.0) is True  # Large amount
        assert is_valid_amount(1) is True  # Integer amounts
    
    def test_invalid_amount(self):
        """Test invalid payment amounts."""
        assert is_valid_amount(0) is False  # Zero amount
        assert is_valid_amount(-10) is False  # Negative amount
        assert is_valid_amount(-0.001) is False  # Negative small amount
