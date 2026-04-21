# Changelog

All notable changes to Stray-SDK will be documented in this file.

## [1.2.0] - 2024-01-21

### Added
- **Menu-driven CLI interface** - Enhanced user experience with intuitive menu system
- **Transaction History** - View recent transactions for any Stellar account
- **Account Creation** - Generate and fund new Stellar accounts automatically
- **Transaction Status Checking** - Verify transaction success and get detailed information
- **Detailed Account Information** - View comprehensive account data including balances, thresholds, and flags
- **Enhanced Error Handling** - Improved error messages with specific recovery suggestions
- **Input Validation Improvements** - Better validation for all user inputs
- **Comprehensive Test Suite** - Added extensive tests for all new features

### Enhanced
- **CLI User Experience** - Replaced simple prompt system with feature-rich menu interface
- **Error Messages** - More descriptive error messages with actionable recovery suggestions
- **Balance Checking** - Enhanced balance validation with liability calculations
- **Transaction Monitoring** - Added detailed transaction status and history tracking
- **Account Management** - Complete account lifecycle support (create, fund, monitor)

### Fixed
- **Error Handling** - Improved exception handling throughout the application
- **User Input Validation** - More robust validation for addresses, amounts, and other inputs
- **Network Error Recovery** - Better handling of network connectivity issues

### Technical Improvements
- **Modular Error Handling** - Separated error handling logic into dedicated utility module
- **Enhanced Type Hints** - Added comprehensive type annotations
- **Test Coverage** - Increased test coverage for new and existing functionality
- **Code Organization** - Better separation of concerns in CLI and client modules

## [1.1.0] - Previous Release

### Features
- Basic XLM payment functionality
- Simple CLI interface
- Environment-based configuration
- Testnet support
- Input validation for addresses and amounts

---

## Migration Guide

### From v1.1 to v1.2

The v1.2 release is fully backward compatible. Existing users will get the enhanced menu interface automatically when running `python main.py`.

**New Features Available:**
1. Run `python main.py` and select from the menu options
2. Use option 3 to create new accounts
3. Use option 2 to view transaction history
4. Use option 5 to check transaction status

**No Configuration Changes Required:**
- Existing `.env` files will continue to work
- All existing functionality preserved
- Enhanced features available automatically
