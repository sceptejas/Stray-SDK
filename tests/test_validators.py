"""Tests for validation utilities."""
import pytest
from stellar_agent.utils.validators import (
    is_valid_stellar_address, 
    is_valid_amount,
    is_valid_secret_key,
    is_valid_xdr,
    get_public_key_from_secret
)

class TestValidators:
    """Test validation functions."""
    
    def test_valid_stellar_address(self):
        """Test valid Stellar address format."""
        valid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(valid_address) is True
    
    def test_invalid_stellar_address_wrong_prefix(self):
        """Test address with wrong prefix."""
        invalid_address = "ABRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(invalid_address) is False
    
    def test_invalid_stellar_address_wrong_length(self):
        """Test address with wrong length."""
        invalid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX"
        assert is_valid_stellar_address(invalid_address) is False
    
    def test_empty_address(self):
        """Test empty address."""
        assert is_valid_stellar_address("") is False
    
    def test_valid_amount(self):
        """Test valid payment amount."""
        assert is_valid_amount(10.5) is True
        assert is_valid_amount(0.0000001) is True
    
    def test_invalid_amount(self):
        """Test invalid payment amounts."""
        assert is_valid_amount(0) is False
        assert is_valid_amount(-10) is False
    
    def test_valid_secret_key(self):
        """Test valid Stellar secret key format."""
        # Test secret key (this is a test key, not real)
        valid_secret = "SCZANGBA5YHTNYVVV4C3U252E2B6P6F5T3U6MM63WBSBZATAQI3EBTQ4"
        assert is_valid_secret_key(valid_secret) is True
    
    def test_invalid_secret_key_wrong_prefix(self):
        """Test secret key with wrong prefix."""
        invalid_secret = "GCZANGBA5YHTNYVVV4C3U252E2B6P6F5T3U6MM63WBSBZATAQI3EBTQ4"
        assert is_valid_secret_key(invalid_secret) is False
    
    def test_invalid_secret_key_wrong_length(self):
        """Test secret key with wrong length."""
        invalid_secret = "SCZANGBA5YHTNYVVV4C3U252E2B6P6F5T3U6MM63WBSBZATAQI3EBT"
        assert is_valid_secret_key(invalid_secret) is False
    
    def test_empty_secret_key(self):
        """Test empty secret key."""
        assert is_valid_secret_key("") is False
    
    def test_invalid_secret_key_format(self):
        """Test invalid secret key format."""
        assert is_valid_secret_key("invalid-key") is False
        assert is_valid_secret_key("SCZANGBA5YHTNYVVV4C3U252E2B6P6F5T3U6MM63WBSBZATAQI3EBTQ!") is False
    
    def test_valid_xdr_format(self):
        """Test XDR validation (basic format check)."""
        # Note: This test requires a real XDR string which is complex to generate
        # For now, we test the function exists and handles invalid input correctly
        assert is_valid_xdr("") is False
        assert is_valid_xdr("invalid-xdr") is False
        assert is_valid_xdr(None) is False
    
    def test_get_public_key_from_secret(self):
        """Test getting public key from secret key."""
        # Test with valid secret key
        valid_secret = "SCZANGBA5YHTNYVVV4C3U252E2B6P6F5T3U6MM63WBSBZATAQI3EBTQ4"
        public_key = get_public_key_from_secret(valid_secret)
        
        assert public_key is not None
        assert public_key.startswith('G')
        assert len(public_key) == 56
    
    def test_get_public_key_from_invalid_secret(self):
        """Test getting public key from invalid secret key."""
        assert get_public_key_from_secret("invalid") is None
        assert get_public_key_from_secret("") is None
