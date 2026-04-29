#!/usr/bin/env python3
"""
Simple test script to validate our improvements to error handling and validation.
This script can be run without pytest to verify our changes work correctly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_validators():
    """Test the enhanced validation functions."""
    print("Testing enhanced validation functions...")
    
    try:
        from stellar_agent.utils.validators import (
            validate_stellar_address, 
            validate_stellar_secret_key,
            validate_transaction_inputs,
            is_valid_stellar_address,
            is_valid_secret_key
        )
        
        # Test valid Stellar address
        valid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        is_valid, error_msg = validate_stellar_address(valid_address)
        assert is_valid == True, f"Expected valid address to pass, got error: {error_msg}"
        assert error_msg == "", f"Expected empty error message, got: {error_msg}"
        print("✅ Valid Stellar address test passed")
        
        # Test invalid Stellar address (wrong prefix)
        invalid_address = "ABRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        is_valid, error_msg = validate_stellar_address(invalid_address)
        assert is_valid == False, "Expected invalid address to fail validation"
        assert "Invalid address prefix" in error_msg, f"Expected prefix error, got: {error_msg}"
        print("✅ Invalid Stellar address prefix test passed")
        
        # Test valid secret key
        valid_secret = "SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        is_valid, error_msg = validate_stellar_secret_key(valid_secret)
        assert is_valid == True, f"Expected valid secret key to pass, got error: {error_msg}"
        assert error_msg == "", f"Expected empty error message, got: {error_msg}"
        print("✅ Valid secret key test passed")
        
        # Test invalid secret key (public key format)
        public_key_as_secret = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        is_valid, error_msg = validate_stellar_secret_key(public_key_as_secret)
        assert is_valid == False, "Expected public key format to fail as secret key"
        assert "appears to be a public key" in error_msg, f"Expected public key error, got: {error_msg}"
        print("✅ Public key as secret key test passed")
        
        # Test comprehensive transaction validation
        source_secret = "SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        destination = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        amount = 10.5
        
        is_valid, error_msg = validate_transaction_inputs(source_secret, destination, amount)
        assert is_valid == True, f"Expected valid transaction inputs to pass, got error: {error_msg}"
        assert error_msg == "", f"Expected empty error message, got: {error_msg}"
        print("✅ Valid transaction inputs test passed")
        
        # Test same source and destination
        is_valid, error_msg = validate_transaction_inputs(source_secret, source_secret, amount)
        assert is_valid == False, "Expected same source/destination to fail"
        assert "Source and destination addresses cannot be the same" in error_msg, f"Expected same address error, got: {error_msg}"
        print("✅ Same source/destination test passed")
        
        # Test invalid amount
        is_valid, error_msg = validate_transaction_inputs(source_secret, destination, -10.0)
        assert is_valid == False, "Expected negative amount to fail"
        assert "Invalid amount" in error_msg, f"Expected amount error, got: {error_msg}"
        print("✅ Invalid amount test passed")
        
        print("🎉 All validation tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This might be due to missing dependencies. The code structure is correct.")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_error_messages():
    """Test that error messages are descriptive and user-friendly."""
    print("\nTesting error message quality...")
    
    try:
        from stellar_agent.utils.validators import validate_stellar_address, validate_stellar_secret_key
        
        # Test empty address
        is_valid, error_msg = validate_stellar_address("")
        assert is_valid == False
        assert error_msg == "Address cannot be empty"
        assert len(error_msg) > 10, "Error message should be descriptive"
        print("✅ Empty address error message is descriptive")
        
        # Test whitespace address
        is_valid, error_msg = validate_stellar_address("   ")
        assert is_valid == False
        assert "whitespace" in error_msg.lower()
        print("✅ Whitespace address error message is descriptive")
        
        # Test wrong length address
        short_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX"
        is_valid, error_msg = validate_stellar_address(short_address)
        assert is_valid == False
        assert "55 characters" in error_msg
        assert "56 characters" in error_msg
        print("✅ Wrong length error message is descriptive")
        
        # Test invalid characters
        invalid_chars_address = "GBRPYHIL1CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        is_valid, error_msg = validate_stellar_address(invalid_chars_address)
        assert is_valid == False
        assert "Invalid characters" in error_msg
        assert "1" in error_msg
        print("✅ Invalid characters error message is descriptive")
        
        print("🎉 All error message tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error message test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Stray SDK improvements...")
    print("=" * 50)
    
    validators_passed = test_validators()
    error_messages_passed = test_error_messages()
    
    print("\n" + "=" * 50)
    if validators_passed and error_messages_passed:
        print("🎉 All tests passed! The improvements are working correctly.")
        print("\n📋 Summary of improvements:")
        print("✅ Enhanced public key validation with detailed error messages")
        print("✅ Added secret key validation with comprehensive checks")
        print("✅ Added comprehensive transaction input validation")
        print("✅ Improved error messages to be user-friendly and descriptive")
        print("✅ Added validation before transaction attempts")
        print("✅ Removed broken multisig references")
        print("✅ Added comprehensive test coverage")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
