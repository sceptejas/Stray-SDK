#!/usr/bin/env python3
"""
Example demonstrating multi-signature transaction workflow with Stray-SDK.

This example shows how to:
1. Create a multi-signature account
2. Build and sign a multi-signature transaction
3. Submit the transaction when enough signatures are collected

Note: This is for demonstration purposes. In production, you would need
to coordinate with other signers to collect their signatures.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path to import stellar_agent
sys.path.insert(0, str(Path(__file__).parent.parent))

from stellar_agent.multisig import MultiSigManager, Signer, PendingTransaction
from stellar_agent.utils.validators import (
    is_valid_stellar_address, is_valid_secret_key, 
    is_valid_weight, is_valid_threshold
)
from stellar_sdk import Keypair


def create_example_multisig_account():
    """Example of creating a multi-signature account."""
    print("=== Creating Multi-Signature Account Example ===\n")
    
    # Initialize the multi-signature manager
    manager = MultiSigManager()
    
    # Example configuration (in practice, these would come from user input)
    master_secret = "SAB5556GTX2M3RSLYYVZHHVUHDZ5Y6VFVQ2DEG2QI3X5D2L7N4QBJD5K"
    
    # Create example signers
    signers = [
        Signer(
            public_key="GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            weight=1
        ),
        Signer(
            public_key="GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2",
            weight=1
        ),
        Signer(
            public_key="GA5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2",
            weight=2
        )
    ]
    
    threshold = 2
    starting_balance = 1.0
    
    print(f"Master Account: {Keypair.from_secret(master_secret).public_key}")
    print(f"Signers:")
    for i, signer in enumerate(signers, 1):
        print(f"  {i}. {signer.public_key} (weight: {signer.weight})")
    print(f"Threshold: {threshold}")
    print(f"Starting Balance: {starting_balance} XLM\n")
    
    try:
        # Create the multi-signature account
        result = manager.create_multisig_account(
            master_secret=master_secret,
            signers=signers,
            threshold=threshold,
            starting_balance=starting_balance
        )
        
        print("✅ Multi-signature account created successfully!")
        print(f"Account ID: {result['account_id']}")
        print(f"Secret Key: {result['secret']}")
        print(f"Threshold: {result['threshold']}")
        print("Signers:")
        for signer in result['signers']:
            print(f"  - {signer['public_key']} (weight: {signer['weight']})")
        
        return result['account_id']
        
    except Exception as e:
        print(f"❌ Error creating multi-signature account: {e}")
        return None


def demonstrate_multisig_transaction(account_id):
    """Example of building and signing a multi-signature transaction."""
    print("\n=== Multi-Signature Transaction Example ===\n")
    
    manager = MultiSigManager()
    
    # Transaction details
    destination = "GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2"
    amount = 0.5
    
    print(f"Source Account: {account_id}")
    print(f"Destination: {destination}")
    print(f"Amount: {amount} XLM\n")
    
    try:
        # Build the transaction
        pending_tx = manager.build_multisig_transaction(
            source_account_id=account_id,
            destination=destination,
            amount=amount,
            description=f"Send {amount} XLM to {destination}"
        )
        
        print("✅ Transaction built successfully!")
        print(f"Description: {pending_tx.description}")
        print(f"Required signatures: {len(pending_tx.required_signatures)}")
        print("Required signers:")
        for signer in pending_tx.required_signatures:
            print(f"  - {signer}")
        print(f"Transaction XDR: {pending_tx.transaction_xdr[:100]}...\n")
        
        # Simulate collecting signatures
        print("=== Signature Collection Simulation ===\n")
        
        # Example signer secrets (in practice, these would be provided by each signer)
        signer_secrets = [
            "SAB5556GTX2M3RSLYYVZHHVUHDZ5Y6VFVQ2DEG2QI3X5D2L7N4QBJD5K",  # Master
            "SCYHMQNU7XXXXXXX2SA3QQU2GA27JS6W47VL74JM45IDKDYVIELIRVQQ",  # Signer 1
            "SA6XSTJ2K5E7L5K5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F"   # Signer 2
        ]
        
        updated_tx = pending_tx
        
        for i, secret in enumerate(signer_secrets):
            try:
                signer_keypair = Keypair.from_secret(secret)
                signer_public = signer_keypair.public_key
                
                if signer_public in updated_tx.required_signatures and signer_public not in updated_tx.collected_signatures:
                    print(f"Adding signature from: {signer_public}")
                    updated_tx = manager.add_signature(updated_tx, secret)
                    print(f"✅ Signature added! Collected: {len(updated_tx.collected_signatures)}/{len(updated_tx.required_signatures)}")
                    
                    # Check if we have enough signatures
                    account_info = manager.server.accounts().account_id(account_id).call()
                    threshold = account_info.get('thresholds', {}).get('med_threshold', 1)
                    
                    if len(updated_tx.collected_signatures) >= threshold:
                        print("✅ Sufficient signatures collected!")
                        break
                else:
                    print(f"Signer {signer_public} not required or already signed")
                    
            except Exception as e:
                print(f"❌ Error adding signature {i+1}: {e}")
        
        # Check if ready to submit
        account_info = manager.server.accounts().account_id(account_id).call()
        threshold = account_info.get('thresholds', {}).get('med_threshold', 1)
        
        if len(updated_tx.collected_signatures) >= threshold:
            print(f"\n=== Submitting Transaction ===\n")
            try:
                response = manager.submit_multisig_transaction(updated_tx)
                print("✅ Transaction submitted successfully!")
                print(f"Transaction Hash: {response['hash']}")
                if 'ledger' in response:
                    print(f"Ledger: {response['ledger']}")
            except Exception as e:
                print(f"❌ Error submitting transaction: {e}")
        else:
            print(f"\n⏳ Need {threshold - len(updated_tx.collected_signatures)} more signatures")
            print("Share this transaction XDR with other signers:")
            print(updated_tx.transaction_xdr)
        
    except Exception as e:
        print(f"❌ Error with multi-signature transaction: {e}")


def check_account_setup(account_id):
    """Example of checking multi-signature account setup."""
    print("\n=== Account Setup Verification ===\n")
    
    manager = MultiSigManager()
    
    try:
        # Get account signers
        signers_info = manager.get_account_signers(account_id)
        
        print(f"Account: {account_id}")
        print(f"Thresholds: {signers_info['thresholds']}")
        print("\nSigners:")
        for signer in signers_info['signers']:
            print(f"  - {signer['public_key']} (weight: {signer['weight']})")
        
        # Validate setup
        is_valid, message = manager.validate_multisig_setup(account_id)
        if is_valid:
            print("\n✅ Multi-signature setup is valid")
        else:
            print(f"\n⚠️  {message}")
        
    except Exception as e:
        print(f"❌ Error checking account setup: {e}")


def main():
    """Main example function."""
    print("Stray-SDK Multi-Signature Example")
    print("================================\n")
    
    print("This example demonstrates the multi-signature functionality.")
    print("Note: This uses testnet and example keys for demonstration.\n")
    
    # Step 1: Create multi-signature account
    account_id = create_example_multisig_account()
    
    if account_id:
        # Step 2: Check account setup
        check_account_setup(account_id)
        
        # Step 3: Demonstrate transaction workflow
        demonstrate_multisig_transaction(account_id)
    
    print("\n=== Example Complete ===")
    print("To use multi-signature features in your own code:")
    print("1. Import MultiSigManager, Signer, and PendingTransaction")
    print("2. Create a MultiSigManager instance")
    print("3. Use create_multisig_account() to set up accounts")
    print("4. Use build_multisig_transaction() to create transactions")
    print("5. Use add_signature() to collect signatures")
    print("6. Use submit_multisig_transaction() when ready")


if __name__ == "__main__":
    main()
