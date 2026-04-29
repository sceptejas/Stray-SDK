"""Unit tests for multi-signature validators."""
import pytest
from stellar_agent.utils.validators import (
    is_valid_secret_key, is_valid_weight, is_valid_threshold,
    validate_signer_configuration
)


class TestSecretKeyValidator:
    """Test secret key validation."""
    
    def test_valid_secret_key(self):
        valid_keys = [
            "SAB5556GTX2M3RSLYYVZHHVUHDZ5Y6VFVQ2DEG2QI3X5D2L7N4QBJD5K",
            "SCYHMQNU7XXXXXXX2SA3QQU2GA27JS6W47VL74JM45IDKDYVIELIRVQQ",
            "SA6XSTJ2K5E7L5K5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F"
        ]
        
        for key in valid_keys:
            assert is_valid_secret_key(key) is True
    
    def test_invalid_secret_key(self):
        invalid_keys = [
            "",  # Empty
            "INVALID",  # Wrong format
            "GAB5556GTX2M3RSLYYVZHHVUHDZ5Y6VFVQ2DEG2QI3X5D2L7N4QBJD5K",  # Starts with G
            "SAB5556GTX2M3RSLYYVZHHVUHDZ5Y6VFVQ2DEG2QI3X5D2L7N4QBJD",  # Too short
            "SAB5556GTX2M3RSLYYVZHHVUHDZ5Y6VFVQ2DEG2QI3X5D2L7N4QBJD5KX",  # Too long
            "SAB5556GTX2M3RSLYYVZHHVUHDZ5Y6VFVQ2DEG2QI3X5D2L7N4QBJD5!"  # Invalid character
        ]
        
        for key in invalid_keys:
            assert is_valid_secret_key(key) is False


class TestWeightValidator:
    """Test weight validation."""
    
    def test_valid_weights(self):
        valid_weights = [1, 2, 10, 100, 255]
        
        for weight in valid_weights:
            assert is_valid_weight(weight) is True
    
    def test_invalid_weights(self):
        invalid_weights = [0, -1, 256, 1000]
        
        for weight in invalid_weights:
            assert is_valid_weight(weight) is False


class TestThresholdValidator:
    """Test threshold validation."""
    
    def test_valid_thresholds(self):
        valid_thresholds = [1, 2, 10, 100, 255]
        
        for threshold in valid_thresholds:
            assert is_valid_threshold(threshold) is True
    
    def test_invalid_thresholds(self):
        invalid_thresholds = [0, -1, 256, 1000]
        
        for threshold in invalid_thresholds:
            assert is_valid_threshold(threshold) is False


class TestSignerConfigurationValidator:
    """Test signer configuration validation."""
    
    def test_valid_configuration(self):
        signers = [
            {'public_key': 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H', 'weight': 1},
            {'public_key': 'GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2', 'weight': 2},
            {'public_key': 'GA5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2', 'weight': 1}
        ]
        threshold = 2
        
        is_valid, error = validate_signer_configuration(signers, threshold)
        assert is_valid is True
        assert error == ""
    
    def test_no_signers(self):
        signers = []
        threshold = 1
        
        is_valid, error = validate_signer_configuration(signers, threshold)
        assert is_valid is False
        assert "At least one signer is required" in error
    
    def test_too_many_signers(self):
        signers = [
            {'public_key': f'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2{i}', 'weight': 1}
            for i in range(21)  # 21 signers, max is 20
        ]
        threshold = 11
        
        is_valid, error = validate_signer_configuration(signers, threshold)
        assert is_valid is False
        assert "Maximum 20 signers allowed" in error
    
    def test_invalid_public_key(self):
        signers = [
            {'public_key': 'INVALID_ADDRESS', 'weight': 1}
        ]
        threshold = 1
        
        is_valid, error = validate_signer_configuration(signers, threshold)
        assert is_valid is False
        assert "Invalid signer address" in error
    
    def test_invalid_weight(self):
        signers = [
            {'public_key': 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H', 'weight': 0}
        ]
        threshold = 1
        
        is_valid, error = validate_signer_configuration(signers, threshold)
        assert is_valid is False
        assert "Invalid weight" in error
    
    def test_insufficient_total_weight(self):
        signers = [
            {'public_key': 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H', 'weight': 1},
            {'public_key': 'GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2', 'weight': 1}
        ]
        threshold = 3  # Total weight is 2, threshold is 3
        
        is_valid, error = validate_signer_configuration(signers, threshold)
        assert is_valid is False
        assert "Total signer weight (2) is less than threshold (3)" in error
    
    def test_edge_case_exact_threshold(self):
        signers = [
            {'public_key': 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H', 'weight': 2},
            {'public_key': 'GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2', 'weight': 1}
        ]
        threshold = 3  # Total weight is exactly 3
        
        is_valid, error = validate_signer_configuration(signers, threshold)
        assert is_valid is True
        assert error == ""
    
    def test_mixed_valid_invalid_signers(self):
        signers = [
            {'public_key': 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H', 'weight': 1},
            {'public_key': 'INVALID', 'weight': 1},
            {'public_key': 'GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2', 'weight': 2}
        ]
        threshold = 2
        
        is_valid, error = validate_signer_configuration(signers, threshold)
        assert is_valid is False
        assert "Invalid signer address: INVALID" in error
