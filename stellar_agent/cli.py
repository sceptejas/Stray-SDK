"""Command-line interface for Stellar Agent."""
import sys
from .client import StellarClient
from .config import config
from .utils.validators import is_valid_stellar_address, is_valid_amount
from .history import display_transaction_history, display_transaction_summary

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
        print("Commands: 'send' | 'history' | 'exit'")
        command = input("Enter command: ").strip().lower()
        
        if command == "exit":
            break
        
        elif command == "history":
            view_transaction_history(client)
            continue
        
        elif command != "send":
            print("❌ Invalid command. Use 'send', 'history', or 'exit'")
            continue
        
        # Send payment flow
        destination = input("Enter destination public key: ").strip()
        
        if not destination:
            print("❌ Destination cannot be empty")
            continue
        
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

def view_transaction_history(client):
    """View transaction history for an account."""
    try:
        # Get account to view history for
        print("\n📜 Transaction History Viewer")
        account_choice = input("View history for: (1) Your account (2) Another account: ").strip()
        
        if account_choice == "1":
            account_id = config.get_source_public_key()
            print(f"Fetching history for your account: {account_id[:8]}...{account_id[-8:]}")
        elif account_choice == "2":
            account_id = input("Enter account public key: ").strip()
            if not is_valid_stellar_address(account_id):
                print("❌ Invalid Stellar address.")
                return
        else:
            print("❌ Invalid choice.")
            return
        
        # Get number of transactions to fetch
        limit_input = input("Number of transactions to fetch (default 10, max 50): ").strip()
        try:
            limit = int(limit_input) if limit_input else 10
            limit = min(max(1, limit), 50)  # Clamp between 1 and 50
        except ValueError:
            limit = 10
        
        # Fetch and display history
        print(f"\n⏳ Fetching last {limit} transactions...")
        transactions = client.get_transaction_history(account_id, limit=limit)
        
        if transactions:
            display_transaction_history(transactions, account_id)
            
            # Ask if user wants summary
            show_summary = input("\nShow summary statistics? (y/n): ").strip().lower()
            if show_summary == 'y':
                display_transaction_summary(transactions, account_id)
        else:
            print("\n📭 No transactions found for this account.")
            
    except RuntimeError as e:
        print(f"❌ Error fetching history: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def run():
    """Entry point for the CLI."""
    prompt_and_send()
