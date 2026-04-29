"""Simple syntax and import validation script."""

import sys
import os

def test_imports():
    """Test if all imports work correctly."""
    try:
        # Test importing the validators module
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stellar_agent'))
        from utils.validators import validate_stellar_address, is_valid_stellar_address
        print("✅ Imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of the validation."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stellar_agent'))
        from utils.validators import validate_stellar_address, is_valid_stellar_address
        
        # Test valid address
        valid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        is_valid, error_msg = validate_stellar_address(valid_address)
        assert is_valid == True, f"Expected valid address to pass, got error: {error_msg}"
        assert error_msg == "", f"Expected empty error message for valid address, got: {error_msg}"
        
        # Test invalid address (wrong prefix)
        invalid_address = "ABRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        is_valid, error_msg = validate_stellar_address(invalid_address)
        assert is_valid == False, f"Expected invalid address to fail"
        assert "prefix" in error_msg.lower(), f"Expected prefix error, got: {error_msg}"
        
        # Test backward compatibility
        assert is_valid_stellar_address(valid_address) == True
        assert is_valid_stellar_address(invalid_address) == False
        
        print("✅ Basic functionality tests passed")
        return True
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Stellar address validation implementation...")
    
    imports_ok = test_imports()
    functionality_ok = test_basic_functionality()
    
    if imports_ok and functionality_ok:
        print("\n✅ All tests passed! Implementation appears to be working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
