#!/usr/bin/env python3
"""Simple test script to validate the enhanced Stellar address validation."""

import sys
import os

# Add the stellar_agent module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from stellar_agent.utils.validators import validate_stellar_address, is_valid_stellar_address

def test_validation():
    """Test the validation functions."""
    print("Testing enhanced Stellar address validation...")
    
    # Test cases: (address, expected_valid, should_contain_error)
    test_cases = [
        # Valid address
        ("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", True, ""),
        
        # Empty/None cases
        ("", False, "cannot be empty"),
        (None, False, "cannot be empty"),
        ("   ", False, "whitespace only"),
        
        # Length issues
        ("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX", False, "55 characters"),
        ("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2HH", False, "57 characters"),
        
        # Prefix issues
        ("SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", False, "secret key"),
        ("ABRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", False, "prefix: 'A'"),
        ("1BRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", False, "must start with 'G'"),
        
        # Character issues
        ("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2I", False, "Invalid characters: I"),
        ("GBRPYHIL1CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", False, "Invalid characters: 1, 8"),
        ("gbrpyhil2ci3fnq4bxlfmndlfjunpu2hy3zmfshonceoasw7qc7ox2h", False, "Invalid characters"),
        
        # Whitespace issues
        (" GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H ", False, "leading or trailing whitespace"),
        
        # Non-string
        (12345, False, "must be a string"),
    ]
    
    passed = 0
    failed = 0
    
    for address, expected_valid, error_contains in test_cases:
        try:
            is_valid, error_msg = validate_stellar_address(address)
            
            if is_valid == expected_valid and error_contains in error_msg:
                print(f"✅ PASS: {address[:20]}... -> {is_valid}")
                passed += 1
            else:
                print(f"❌ FAIL: {address[:20]}... -> Expected valid={expected_valid}, got {is_valid}")
                print(f"   Expected error to contain: '{error_contains}'")
                print(f"   Actual error: '{error_msg}'")
                failed += 1
        except Exception as e:
            print(f"❌ ERROR: {address[:20]}... -> Exception: {e}")
            failed += 1
    
    print(f"\n--- Results ---")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    
    # Test backward compatibility
    print(f"\n--- Backward Compatibility Test ---")
    try:
        assert is_valid_stellar_address("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H") == True
        assert is_valid_stellar_address("ABRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H") == False
        assert is_valid_stellar_address("") == False
        print("✅ Backward compatibility: PASS")
        passed += 1
    except Exception as e:
        print(f"❌ Backward compatibility: FAIL - {e}")
        failed += 1
    
    return failed == 0

if __name__ == "__main__":
    success = test_validation()
    sys.exit(0 if success else 1)
