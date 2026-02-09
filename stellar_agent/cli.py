"""Command-line interface for Stellar Agent."""
import sys
from .client import StellarClient, MultisigInfo
from .config import config
from .utils.validators import (
    is_valid_stellar_address, 
    is_valid_amount, 
    is_valid_secret_key, 
    is_valid_xdr,
    get_public_key_from_secret
)

def show_multisig_info():
    """Show multisig information for an account."""
    client = StellarClient()
    
    account_input = input("Enter account public key: ").strip()
    
    if not is_valid_stellar_address(account_input):
        print("❌ Invalid Stellar address. Must start with 'G' and be 56 characters long.")
        return
    
    try:
        multisig_info = client.get_multisig_info(account_input)
        
        print(f"\n--- Multisig Information for {account_input[:8]}...{account_input[-8:]} ---")
        print(f"Required threshold: {multisig_info.required_threshold}")
        print(f"Total signing weight: {multisig_info.current_weight}")
        print(f"Multisig required: {'Yes' if multisig_info.is_multisig_required else 'No'}")
        
        if multisig_info.signers:
            print(f"\nSigners ({len(multisig_info.signers)}):")
            for i, signer in enumerate(multisig_info.signers, 1):
                key = signer.get('key', 'Unknown')
                weight = signer.get('weight', 0)
                print(f"  {i}. {key[:8]}...{key[-8:]} (weight: {weight})")
        else:
            print("No signers found")
            
    except Exception as e:
        print(f"❌ Error fetching account info: {str(e)}")


def build_transaction():
    """Build a transaction without submitting it."""
    client = StellarClient()
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please set SOURCE_SECRET in your environment variables or .env file")
        return
    
    destination = input("Enter destination public key: ").strip()
    
    if not is_valid_stellar_address(destination):
        print("❌ Invalid Stellar address. Must start with 'G' and be 56 characters long.")
        return
    
    amount_str = input("Enter amount to send (in XLM): ").strip()
    
    try:
        amount = float(amount_str)
        if not is_valid_amount(amount):
            print("❌ Amount must be positive.")
            return
    except ValueError:
        print("❌ Invalid amount. Please enter a number.")
        return
    
    try:
        # Build transaction with automatic multisig detection
        transaction, multisig_info = client.build_payment_transaction_smart(
            config.source_secret,
            destination,
            amount
        )
        
        # Get transaction info
        tx_info = client.get_transaction_info(transaction)
        source_public = get_public_key_from_secret(config.source_secret)
        
        print(f"\n--- Transaction Built Successfully ---")
        print(f"From: {source_public[:8]}...{source_public[-8:]}")
        print(f"To: {destination[:8]}...{destination[-8:]}")
        print(f"Amount: {amount} XLM")
        print(f"Signatures: {tx_info['signature_count']}/{tx_info['required_threshold']}")
        
        if multisig_info.is_multisig_required:
            print(f"⚠️  Multisig account detected! Required threshold: {multisig_info.required_threshold}")
            
            if tx_info['is_ready_to_submit']:
                print("✅ Transaction ready to submit!")
                
                submit = input("Submit transaction now? (y/N): ").strip().lower()
                if submit == 'y':
                    response = client.submit_signed_transaction(transaction)
                    print("✅ Transaction Successful!")
                    print("Transaction Hash:", response['hash'])
                    return
            else:
                print(f"❌ Need {tx_info['required_threshold'] - tx_info['signature_count']} more signature(s)")
                print("Use 'sign <xdr>' command to add additional signatures")
        else:
            print("✅ Single signature account - transaction ready to submit!")
            
            submit = input("Submit transaction now? (y/N): ").strip().lower()
            if submit == 'y':
                response = client.submit_signed_transaction(transaction)
                print("✅ Transaction Successful!")
                print("Transaction Hash:", response['hash'])
                return
        
        # Export XDR
        xdr = client.export_transaction_xdr(transaction)
        print(f"\nTransaction XDR:")
        print(xdr)
        
        # Save to file option
        save_file = input("\nSave XDR to file? Enter filename (or press Enter to skip): ").strip()
        if save_file:
            try:
                with open(save_file, 'w') as f:
                    f.write(xdr)
                print(f"✅ XDR saved to {save_file}")
            except Exception as e:
                print(f"❌ Error saving file: {str(e)}")
                
    except Exception as e:
        print(f"❌ Error building transaction: {str(e)}")


def sign_transaction():
    """Add signature to an existing transaction XDR."""
    client = StellarClient()
    
    # Get XDR input
    xdr_input = input("Enter transaction XDR (or filename): ").strip()
    
    # Check if it's a filename
    if len(xdr_input) < 100:  # XDR strings are much longer
        try:
            with open(xdr_input, 'r') as f:
                xdr_string = f.read().strip()
            print(f"✅ Loaded XDR from {xdr_input}")
        except FileNotFoundError:
            print(f"❌ File '{xdr_input}' not found")
            return
        except Exception as e:
            print(f"❌ Error reading file: {str(e)}")
            return
    else:
        xdr_string = xdr_input
    
    # Validate XDR
    if not is_valid_xdr(xdr_string):
        print("❌ Invalid XDR format")
        return
    
    # Get secret key
    secret_key = input("Enter secret key to sign with: ").strip()
    
    if not is_valid_secret_key(secret_key):
        print("❌ Invalid secret key format")
        return
    
    try:
        # Import transaction
        transaction = client.import_transaction_xdr(xdr_string)
        
        # Show current transaction info
        tx_info = client.get_transaction_info(transaction)
        signer_public = get_public_key_from_secret(secret_key)
        
        print(f"\n--- Transaction Info ---")
        print(f"Source: {tx_info['source_account'][:8]}...{tx_info['source_account'][-8:]}")
        print(f"Current signatures: {tx_info['signature_count']}/{tx_info['required_threshold']}")
        print(f"Signing with: {signer_public[:8]}...{signer_public[-8:]}")
        
        # Add signature
        signed_transaction = client.add_signature_to_transaction(transaction, secret_key)
        
        # Get updated info
        updated_info = client.get_transaction_info(signed_transaction)
        
        print(f"\n--- After Signing ---")
        print(f"Signatures: {updated_info['signature_count']}/{updated_info['required_threshold']}")
        
        if updated_info['is_ready_to_submit']:
            print("✅ Transaction ready to submit!")
            
            submit = input("Submit transaction now? (y/N): ").strip().lower()
            if submit == 'y':
                response = client.submit_signed_transaction(signed_transaction)
                print("✅ Transaction Successful!")
                print("Transaction Hash:", response['hash'])
                return
        else:
            needed = updated_info['required_threshold'] - updated_info['signature_count'] 
            print(f"❌ Need {needed} more signature(s)")
        
        # Export updated XDR
        new_xdr = client.export_transaction_xdr(signed_transaction)
        print(f"\nUpdated Transaction XDR:")
        print(new_xdr)
        
        # Save to file option
        save_file = input("\nSave updated XDR to file? Enter filename (or press Enter to skip): ").strip()
        if save_file:
            try:
                with open(save_file, 'w') as f:
                    f.write(new_xdr)
                print(f"✅ Updated XDR saved to {save_file}")
            except Exception as e:
                print(f"❌ Error saving file: {str(e)}")
                
    except Exception as e:
        print(f"❌ Error signing transaction: {str(e)}")


def submit_transaction():
    """Submit a fully signed transaction from XDR."""
    client = StellarClient()
    
    # Get XDR input
    xdr_input = input("Enter transaction XDR (or filename): ").strip()
    
    # Check if it's a filename
    if len(xdr_input) < 100:  # XDR strings are much longer
        try:
            with open(xdr_input, 'r') as f:
                xdr_string = f.read().strip()
            print(f"✅ Loaded XDR from {xdr_input}")
        except FileNotFoundError:
            print(f"❌ File '{xdr_input}' not found")
            return
        except Exception as e:
            print(f"❌ Error reading file: {str(e)}")
            return
    else:
        xdr_string = xdr_input
    
    # Validate XDR
    if not is_valid_xdr(xdr_string):
        print("❌ Invalid XDR format")
        return
    
    try:
        # Import transaction
        transaction = client.import_transaction_xdr(xdr_string)
        
        # Check if ready to submit
        can_submit, reason = client.can_submit_transaction(transaction)
        tx_info = client.get_transaction_info(transaction)
        
        print(f"\n--- Transaction Info ---")
        print(f"Source: {tx_info['source_account'][:8]}...{tx_info['source_account'][-8:]}")
        print(f"Signatures: {tx_info['signature_count']}/{tx_info['required_threshold']}")
        print(f"Status: {reason}")
        
        if not can_submit:
            print("❌ Cannot submit transaction - insufficient signatures")
            return
        
        # Confirm submission
        confirm = input("\nSubmit transaction? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Transaction submission cancelled")
            return
        
        # Submit
        response = client.submit_signed_transaction(transaction)
        print("✅ Transaction Successful!")
        print("Transaction Hash:", response['hash'])
        
    except Exception as e:
        print(f"❌ Error submitting transaction: {str(e)}")


def show_transaction_info():
    """Show information about a transaction XDR."""
    client = StellarClient()
    
    # Get XDR input
    xdr_input = input("Enter transaction XDR (or filename): ").strip()
    
    # Check if it's a filename
    if len(xdr_input) < 100:  # XDR strings are much longer
        try:
            with open(xdr_input, 'r') as f:
                xdr_string = f.read().strip()
            print(f"✅ Loaded XDR from {xdr_input}")
        except FileNotFoundError:
            print(f"❌ File '{xdr_input}' not found")
            return
        except Exception as e:
            print(f"❌ Error reading file: {str(e)}")
            return
    else:
        xdr_string = xdr_input
    
    # Validate XDR
    if not is_valid_xdr(xdr_string):
        print("❌ Invalid XDR format")
        return
    
    try:
        # Import transaction and get info
        transaction = client.import_transaction_xdr(xdr_string)
        tx_info = client.get_transaction_info(transaction)
        
        print(f"\n--- Transaction Information ---")
        print(f"Source Account: {tx_info['source_account']}")
        print(f"Sequence Number: {tx_info['sequence_number']}")
        print(f"Fee: {tx_info['fee']} stroops")
        print(f"Operations: {tx_info['operations_count']}")
        print(f"Current Signatures: {tx_info['signature_count']}")
        print(f"Required Threshold: {tx_info['required_threshold']}")
        print(f"Ready to Submit: {'Yes' if tx_info['is_ready_to_submit'] else 'No'}")
        
        if tx_info['needs_more_signatures']:
            needed = tx_info['required_threshold'] - tx_info['signature_count']
            print(f"Additional Signatures Needed: {needed}")
        
    except Exception as e:
        print(f"❌ Error analyzing transaction: {str(e)}")


def show_help():
    """Show help information."""
    print("\n--- Stellar Agent CLI Commands ---")
    print("1. send         - Interactive payment (supports both single and multisig)")
    print("2. build        - Build transaction without submitting")
    print("3. sign         - Add signature to existing transaction XDR")
    print("4. submit       - Submit fully signed transaction")
    print("5. info         - Show transaction information from XDR")
    print("6. multisig     - Show multisig information for account")
    print("7. help         - Show this help")
    print("8. exit         - Exit the application")
    
    print("\n--- Multisig Workflow ---")
    print("1. Use 'build' to create transaction and get XDR")
    print("2. Share XDR with other signers")
    print("3. Each signer uses 'sign <xdr>' to add their signature")
    print("4. Use 'submit <final_xdr>' when enough signatures collected")
    
    print("\n--- Tips ---")
    print("• XDR can be provided directly or as filename")
    print("• Use 'info' command to check signature status")
    print("• Accounts with threshold > 1 require multisig")


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
        
        # Validate destination address
        if not is_valid_stellar_address(destination):
            print("❌ Invalid Stellar address. Must start with 'G' and be 56 characters long.")
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
        
        print(f"Sending {amount} XLM to {destination}...")
        try:
            response = client.send_payment(config.source_secret, destination, amount)
            print("✅ Transaction Successful!")
            print("Transaction Hash:", response['hash'])
        except Exception as e:
            print("❌ Transaction Failed:", str(e))

def run():
    """Entry point for the CLI."""
    # Check if command-line arguments are provided
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "help":
            show_help()
        elif command == "multisig":
            show_multisig_info()
        elif command == "build":
            build_transaction()
        elif command == "sign":
            if len(sys.argv) > 2:
                # Quick sign mode: stellar_agent sign <xdr>
                print("Quick sign mode not implemented in interactive CLI")
                print("Use interactive mode by running 'python main.py sign'")
            else:
                sign_transaction()
        elif command == "submit":
            if len(sys.argv) > 2:
                # Quick submit mode: stellar_agent submit <xdr>
                print("Quick submit mode not implemented in interactive CLI")
                print("Use interactive mode by running 'python main.py submit'")
            else:
                submit_transaction()
        elif command == "info":
            show_transaction_info()
        elif command == "send":
            prompt_and_send()
        else:
            print(f"Unknown command: {command}")
            show_help()
    else:
        # Interactive mode
        main_menu()


def main_menu():
    """Interactive main menu."""
    print("🌟 Stellar Agent CLI - Multi-signature Support")
    print("Type 'help' for available commands")
    
    while True:
        print()
        command = input("stellar-agent> ").strip().lower()
        
        if command == "exit" or command == "quit":
            print("Goodbye! 👋")
            break
        elif command == "help":
            show_help()
        elif command == "send":
            prompt_and_send()
        elif command == "build":
            build_transaction()
        elif command == "sign":
            sign_transaction()
        elif command == "submit":
            submit_transaction()
        elif command == "info":
            show_transaction_info()
        elif command == "multisig":
            show_multisig_info()
        elif command == "":
            continue  # Empty command, just show prompt again
        else:
            print(f"Unknown command: '{command}'. Type 'help' for available commands.")
