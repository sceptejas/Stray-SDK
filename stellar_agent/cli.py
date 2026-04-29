"""Command-line interface for Stellar Agent."""
from .client import StellarClient
from .config import config
from .utils.validators import (
    is_valid_stellar_address, validate_stellar_address, is_valid_amount, is_valid_secret_key, 
    is_valid_weight, is_valid_threshold, validate_signer_configuration
)
from .multisig import MultiSigManager, Signer, PendingTransaction

def prompt_and_send():
    """Interactive CLI for sending Stellar payments."""
    client = StellarClient()
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please set SOURCE_SECRET in your environment variables or .env file")
        return
    
    while True:
        print("\n--- Stellar Agent ---")
        destination = input("Enter destination public key (or type 'exit' to quit): ").strip()
        
        if destination.lower() == "exit":
            break
        
        # Validate destination address with detailed error messages
        is_valid, error_msg = validate_stellar_address(destination)
        if not is_valid:
            print(f"❌ Invalid Stellar address: {error_msg}")
            continue
        
        amount_str = input("Enter amount to send (in XLM): ").strip()
        
        try:
            amount = float(amount_str)
            if not is_valid_amount(amount):
                print("❌ Amount must be positive.")
                continue
        except ValueError:
            print("❌ Invalid amount. Please enter a number.")
            continue
        
        # Check balance before attempting payment (if enabled)
        if config.balance_check_enabled:
            try:
                source_public_key = config.get_source_public_key()
                sufficient, current_balance, error_msg = client.check_sufficient_balance(source_public_key, amount)
                
                if not sufficient:
                    print(f"❌ {error_msg}")
                    print(f"💡 Please check: account funding, network connectivity, or reduce payment amount.")
                    continue
                else:
                    print(f"💰 Current balance: {current_balance} XLM (sufficient for payment)")
            except Exception as e:
                print(f"⚠️  Warning: Could not verify balance: {e}")
                print("Proceeding with payment attempt...")
        
        print(f"Sending {amount} XLM to {destination}...")
        try:
            response = client.send_payment(config.source_secret, destination, amount)
            print("✅ Transaction Successful!")
            print("Transaction Hash:", response['hash'])
            if 'ledger' in response:
                print("Ledger:", response['ledger'])
        except RuntimeError as e:
            print(f"❌ Transaction Failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("💡 Please check your network connectivity and configuration.")

<<<<<<< HEAD
=======
def prompt_multisig_menu():
    """Interactive CLI for multi-signature operations."""
    multisig_manager = MultiSigManager()
    
    while True:
        print("\n--- Multi-Signature Operations ---")
        print("1. Create Multi-Signature Account")
        print("2. Send Multi-Signature Payment")
        print("3. Sign Pending Transaction")
        print("4. Check Account Signers")
        print("5. Back to Main Menu")
        
        choice = input("Select an option (1-5): ").strip()
        
        if choice == "1":
            create_multisig_account_workflow(multisig_manager)
        elif choice == "2":
            send_multisig_payment_workflow(multisig_manager)
        elif choice == "3":
            sign_transaction_workflow(multisig_manager)
        elif choice == "4":
            check_account_signers_workflow(multisig_manager)
        elif choice == "5":
            break
        else:
            print("❌ Invalid option. Please select 1-5.")

def create_multisig_account_workflow(manager: MultiSigManager):
    """Workflow for creating a multi-signature account."""
    print("\n--- Create Multi-Signature Account ---")
    
    try:
        # Get master account
        master_secret = input("Enter master account secret key: ").strip()
        if not is_valid_secret_key(master_secret):
            print("❌ Invalid secret key format")
            return
        
        # Get signers
        signers = []
        print("\nAdd signers (enter 'done' when finished):")
        
        while True:
            signer_input = input(f"Signer {len(signers) + 1} public key (or 'done'): ").strip()
            if signer_input.lower() == 'done':
                break
            
            is_valid, error_msg = validate_stellar_address(signer_input)
            if not is_valid:
                print(f"❌ Invalid Stellar address: {error_msg}")
                continue
            
            try:
                weight = int(input(f"Weight for {signer_input} (1-255): ").strip())
                if not is_valid_weight(weight):
                    print("❌ Weight must be between 1 and 255")
                    continue
            except ValueError:
                print("❌ Invalid weight")
                continue
            
            signers.append(Signer(public_key=signer_input, weight=weight))
            print(f"✅ Added signer: {signer_input} (weight: {weight})")
        
        if len(signers) == 0:
            print("❌ At least one signer is required")
            return
        
        # Get threshold
        try:
            threshold = int(input("Enter signature threshold (1-255): ").strip())
            if not is_valid_threshold(threshold):
                print("❌ Threshold must be between 1 and 255")
                return
        except ValueError:
            print("❌ Invalid threshold")
            return
        
        # Get starting balance
        try:
            balance = float(input("Enter starting balance for new account (XLM): ").strip())
            if not is_valid_amount(balance):
                print("❌ Invalid amount")
                return
        except ValueError:
            print("❌ Invalid amount")
            return
        
        # Create account
        print("\nCreating multi-signature account...")
        result = manager.create_multisig_account(master_secret, signers, threshold, balance)
        
        print("✅ Multi-signature account created successfully!")
        print(f"Account ID: {result['account_id']}")
        print(f"Secret Key: {result['secret']}")
        print(f"Threshold: {result['threshold']}")
        print("Signers:")
        for signer in result['signers']:
            print(f"  - {signer['public_key']} (weight: {signer['weight']})")
        print("\n⚠️  Save the secret key securely!")
        
    except Exception as e:
        print(f"❌ Failed to create multi-signature account: {e}")

def send_multisig_payment_workflow(manager: MultiSigManager):
    """Workflow for sending a multi-signature payment."""
    print("\n--- Send Multi-Signature Payment ---")
    
    try:
        # Get source account
        source_account = input("Enter multi-signature account ID: ").strip()
        is_valid, error_msg = validate_stellar_address(source_account)
        if not is_valid:
            print(f"❌ Invalid Stellar address: {error_msg}")
            return
        
        # Check if account is multi-signature
        is_valid, message = manager.validate_multisig_setup(source_account)
        if not is_valid:
            print(f"❌ Account is not properly set up for multi-signature: {message}")
            return
        
        # Get destination
        destination = input("Enter destination address: ").strip()
        is_valid, error_msg = validate_stellar_address(destination)
        if not is_valid:
            print(f"❌ Invalid Stellar address: {error_msg}")
            return
        
        # Get amount
        try:
            amount = float(input("Enter amount to send (XLM): ").strip())
            if not is_valid_amount(amount):
                print("❌ Invalid amount")
                return
        except ValueError:
            print("❌ Invalid amount")
            return
        
        # Build transaction
        print("\nBuilding multi-signature transaction...")
        pending_tx = manager.build_multisig_transaction(source_account, destination, amount)
        
        print("✅ Transaction built successfully!")
        print(f"Description: {pending_tx.description}")
        print(f"Required signatures: {len(pending_tx.required_signatures)}")
        print("Required signers:")
        for signer in pending_tx.required_signatures:
            print(f"  - {signer}")
        
        # Ask if user wants to sign now
        sign_now = input("\nDo you want to sign this transaction now? (y/n): ").strip().lower()
        if sign_now == 'y':
            signer_secret = input("Enter your secret key: ").strip()
            if not is_valid_secret_key(signer_secret):
                print("❌ Invalid secret key format")
                return
            
            updated_tx = manager.add_signature(pending_tx, signer_secret)
            print(f"✅ Signature added! Collected: {len(updated_tx.collected_signatures)}/{len(updated_tx.required_signatures)}")
            
            # Check if ready to submit
            account_info = manager.server.accounts().account_id(source_account).call()
            threshold = account_info.get('thresholds', {}).get('med_threshold', 1)
            
            if len(updated_tx.collected_signatures) >= threshold:
                submit = input("Transaction has enough signatures. Submit now? (y/n): ").strip().lower()
                if submit == 'y':
                    print("Submitting transaction...")
                    response = manager.submit_multisig_transaction(updated_tx)
                    print("✅ Transaction submitted successfully!")
                    print(f"Transaction Hash: {response['hash']}")
                    if 'ledger' in response:
                        print(f"Ledger: {response['ledger']}")
            else:
                print(f"⏳ Need {threshold - len(updated_tx.collected_signatures)} more signatures")
                print("Share the transaction XDR with other signers to collect their signatures:")
                print(updated_tx.transaction_xdr)
        
    except Exception as e:
        print(f"❌ Failed to send multi-signature payment: {e}")

def sign_transaction_workflow(manager: MultiSigManager):
    """Workflow for signing a pending transaction."""
    print("\n--- Sign Pending Transaction ---")
    
    try:
        # Get transaction XDR
        transaction_xdr = input("Enter transaction XDR: ").strip()
        if not transaction_xdr:
            print("❌ Transaction XDR is required")
            return
        
        # Get network passphrase
        network_passphrase = input(f"Enter network passphrase (default: {config.network_passphrase}): ").strip()
        if not network_passphrase:
            network_passphrase = config.network_passphrase
        
        # Create pending transaction object
        pending_tx = PendingTransaction(
            transaction_xdr=transaction_xdr,
            network_passphrase=network_passphrase,
            required_signatures=[],  # Will be populated when loading transaction
            collected_signatures={},
            created_at=0,
            description=""
        )
        
        # Get signer secret
        signer_secret = input("Enter your secret key: ").strip()
        if not is_valid_secret_key(signer_secret):
            print("❌ Invalid secret key format")
            return
        
        # Add signature
        updated_tx = manager.add_signature(pending_tx, signer_secret)
        print("✅ Signature added successfully!")
        
        # Show transaction info
        from stellar_sdk import Transaction
        transaction = Transaction.from_xdr(transaction_xdr, network_passphrase)
        print(f"Source Account: {transaction.source.account_id}")
        print(f"Operations: {len(transaction.operations)}")
        
        # Check if ready to submit
        source_account = transaction.source.account_id
        account_info = manager.server.accounts().account_id(source_account).call()
        threshold = account_info.get('thresholds', {}).get('med_threshold', 1)
        
        # For demonstration, we'll assume we need to estimate signatures
        print(f"Transaction ready for submission when {threshold} signatures are collected")
        print("Updated transaction XDR:")
        print(updated_tx.transaction_xdr)
        
    except Exception as e:
        print(f"❌ Failed to sign transaction: {e}")

def check_account_signers_workflow(manager: MultiSigManager):
    """Workflow for checking account signers."""
    print("\n--- Check Account Signers ---")
    
    try:
        account_id = input("Enter account ID: ").strip()
        is_valid, error_msg = validate_stellar_address(account_id)
        if not is_valid:
            print(f"❌ Invalid Stellar address: {error_msg}")
            return
        
        signers_info = manager.get_account_signers(account_id)
        
        print(f"\nAccount: {account_id}")
        print(f"Thresholds: {signers_info['thresholds']}")
        print("\nSigners:")
        for signer in signers_info['signers']:
            print(f"  - {signer['public_key']} (weight: {signer['weight']})")
        
        # Validate setup
        is_valid, message = manager.validate_multisig_setup(account_id)
        if is_valid:
            print("✅ Multi-signature setup is valid")
        else:
            print(f"⚠️  {message}")
        
    except Exception as e:
        print(f"❌ Failed to check account signers: {e}")

>>>>>>> 1cdcf6c (feat: enhance Stellar public key validation with detailed error messages)
def run():
    """Entry point for the CLI."""
    prompt_and_send()
