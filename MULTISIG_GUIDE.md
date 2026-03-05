# Multi-Signature Support for Stray-SDK

This document describes the new multi-signature transaction support added to the Stray-SDK Python CLI.

## Overview

The enhanced CLI now supports Stellar's native multi-signature functionality, allowing you to:

- Detect when an account requires multiple signatures
- Build transactions without submitting them immediately
- Export/import transactions as XDR for signature collection
- Add signatures incrementally
- Submit transactions only when sufficient signatures are collected

## Quick Start

### Basic Usage (unchanged for single-sig accounts)
```bash
python main.py send
```

### New Commands

#### Interactive Menu
```bash
python main.py
```

This opens an interactive menu with the following commands:
- `send` - Interactive payment (supports both single and multisig)
- `build` - Build transaction without submitting
- `sign` - Add signature to existing transaction XDR
- `submit` - Submit fully signed transaction
- `info` - Show transaction information from XDR
- `multisig` - Show multisig information for account
- `help` - Show available commands

#### Command Line Usage
```bash
python main.py help           # Show help
python main.py multisig       # Check account multisig info
python main.py build          # Build transaction
python main.py sign           # Sign transaction XDR
python main.py submit         # Submit signed transaction
python main.py info           # Get transaction info
```

## Multi-Signature Workflow

### 1. Check Account Requirements
```bash
python main.py multisig
# Enter account: GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H
```

Output example:
```
--- Multisig Information for GBRPYHIL...QC7OX2H ---
Required threshold: 2
Total signing weight: 3
Multisig required: Yes

Signers (3):
  1. GBRPYHIL...QC7OX2H (weight: 1)
  2. GC2BKLYOO...LHCQVGF (weight: 1)  
  3. GDSACLV5A...PMQUDFF (weight: 1)
```

### 2. Build Transaction
```bash
python main.py build
# Follow prompts to enter destination and amount
```

The system will:
- Automatically detect if multisig is required
- Build and sign the transaction with your key
- Export XDR for additional signatures (if needed)
- Optionally save XDR to file

### 3. Collect Additional Signatures
Share the XDR with other signers. Each signer runs:
```bash
python main.py sign
# Enter transaction XDR (or filename): <XDR_STRING_OR_FILENAME>
# Enter secret key to sign with: SXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 4. Submit Final Transaction
Once enough signatures are collected:
```bash
python main.py submit
# Enter transaction XDR (or filename): <FINAL_XDR_WITH_ALL_SIGNATURES>
```

## File-Based Workflow

For easier signature collection, you can save/load XDR to/from files:

```bash
# Build transaction and save XDR
python main.py build
# Save XDR to: transaction.xdr

# Signer 1 adds signature
python main.py sign
# Enter transaction XDR: transaction.xdr
# Save updated XDR to: transaction_signed1.xdr

# Signer 2 adds signature  
python main.py sign
# Enter transaction XDR: transaction_signed1.xdr
# Save updated XDR to: transaction_final.xdr

# Submit final transaction
python main.py submit
# Enter transaction XDR: transaction_final.xdr
```

## Security Best Practices

1. **Never share secret keys** - only share transaction XDR
2. **Verify transaction details** before signing - use `info` command
3. **Use secure channels** to share XDR between signers
4. **Validate source account** before signing transactions
5. **Keep private keys secure** and never store them in code

## Error Handling

The CLI provides clear feedback for common issues:

- **Invalid addresses**: "❌ Invalid Stellar address"
- **Insufficient signatures**: "❌ Need X more signature(s)"
- **Invalid XDR**: "❌ Invalid XDR format"
- **Invalid secret key**: "❌ Invalid secret key format"
- **Cannot submit**: "❌ Cannot submit transaction - insufficient signatures"

## Backward Compatibility

All existing functionality remains unchanged:
- Single-signature accounts work exactly as before
- The original `send` command supports both single and multisig
- Environment variables and configuration remain the same

## Technical Details

### New Validator Functions
- `is_valid_secret_key()` - Validates Stellar secret key format
- `is_valid_xdr()` - Validates XDR transaction format
- `get_public_key_from_secret()` - Extracts public key from secret

### New Client Methods
- `get_multisig_info()` - Get account signature requirements
- `build_payment_transaction()` - Build unsigned/signed transaction
- `export_transaction_xdr()` / `import_transaction_xdr()` - XDR handling
- `add_signature_to_transaction()` - Add signature to existing transaction
- `can_submit_transaction()` - Check if transaction has enough signatures
- `submit_signed_transaction()` - Submit fully signed transaction

### MultisigInfo Class
Provides information about account signature requirements:
- `required_threshold` - Minimum signatures needed
- `current_weight` - Total weight of all signers
- `is_multisig_required` - Boolean indicating if multisig needed
- `needs_additional_signatures` - Boolean indicating if more signatures needed

## Examples

### Single Signature Account (unchanged behavior)
```bash
python main.py send
# Works exactly as before - builds, signs, and submits in one step
```

### Multi-Signature Account
```bash
python main.py build
# Destination: GDSACLV5AYIAKLDDFQG7CDIXHAZ4PMQUDFF3ZFSPVQHPGQQU5WVCF5SR  
# Amount: 100
# ⚠️ Multisig account detected! Required threshold: 2
# ❌ Need 1 more signature(s)
# Transaction XDR: AAAAAGBRPYH...
```

Then share XDR with another signer who runs:
```bash
python main.py sign
# XDR: AAAAAGBRPYH...
# Secret key: SDFD...
# ✅ Transaction ready to submit!
# Submit now? y
# ✅ Transaction Successful!
```

## Troubleshooting

### "Invalid XDR format"
- Check the XDR string is complete and not truncated
- Try loading from file instead of pasting directly

### "Need more signatures"
- Use `info` command to see current signature status
- Contact additional signers to add their signatures

### "Cannot submit transaction"
- Verify all required signatures are present using `info` command
- Check that signature threshold is met

### "Invalid secret key format"
- Stellar secret keys start with 'S' and are 56 characters
- Ensure no extra spaces or characters

For additional help, use the `help` command or contact support.