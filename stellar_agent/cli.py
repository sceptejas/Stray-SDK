"""Command-line interface for Stellar Agent."""
from .client import StellarClient
from .config import config
from .utils.validators import is_valid_stellar_address, is_valid_amount
from stellar_sdk import Keypair

def show_main_menu():
    """Display the main menu options."""
    print("\n" + "="*50)
    print("🌟 STELLAR AGENT - MAIN MENU 🌟")
    print("="*50)
    print("1. 💸 Send Payment")
    print("2. 📜 View Transaction History")
    print("3. 👛 Create New Account")
    print("4. 💰 Check Account Balance")
    print("5. 🔍 Check Transaction Status")
    print("6. ⚙️  Account Details")
    print("7. 🚪 Exit")
    print("="*50)

def send_payment(client):
    """Handle sending payments."""
    print("\n--- Send Payment ---")
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
    
    # Check balance before attempting payment (if enabled)
    if config.balance_check_enabled:
        try:
            source_public_key = config.get_source_public_key()
            sufficient, current_balance, error_msg = client.check_sufficient_balance(source_public_key, amount)
            
            if not sufficient:
                print(f"❌ {error_msg}")
                print(f"💡 Please check: account funding, network connectivity, or reduce payment amount.")
                return
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
    print("\n--- Transaction History ---")
    account_id = input("Enter account public key (leave empty for source account): ").strip()
    
    if not account_id:
        try:
            account_id = config.get_source_public_key()
            print(f"Using source account: {account_id}")
        except Exception as e:
            print(f"❌ Error getting source account: {e}")
            return
    
    if not is_valid_stellar_address(account_id):
        print("❌ Invalid Stellar address.")
        return
    
    limit_str = input("Enter number of transactions to show (default 10): ").strip()
    try:
        limit = int(limit_str) if limit_str else 10
        limit = min(limit, 50)  # Cap at 50 for performance
    except ValueError:
        print("❌ Invalid number. Using default 10.")
        limit = 10
    
    try:
        transactions = client.get_transaction_history(account_id, limit)
        if not transactions:
            print("📝 No transactions found.")
            return
        
        print(f"\n📜 Found {len(transactions)} transactions:")
        print("-" * 80)
        for i, tx in enumerate(transactions, 1):
            print(f"{i}. Hash: {tx.get('hash', 'N/A')[:16]}...")
            print(f"   Type: {tx.get('type', 'N/A')}")
            print(f"   Created: {tx.get('created_at', 'N/A')}")
            print(f"   Successful: {tx.get('successful', 'N/A')}")
            print(f"   Ledger: {tx.get('ledger', 'N/A')}")
            print("-" * 80)
    except Exception as e:
        print(f"❌ Error fetching transaction history: {e}")

def create_new_account(client):
    """Create a new Stellar account."""
    print("\n--- Create New Account ---")
    print("⚠️  This will create a new account and fund it from your source account.")
    
    amount_str = input("Enter starting balance for new account (in XLM, minimum 1.0): ").strip()
    
    try:
        amount = float(amount_str)
        if not is_valid_amount(amount) or amount < 1.0:
            print("❌ Amount must be positive and at least 1.0 XLM.")
            return
    except ValueError:
        print("❌ Invalid amount. Please enter a number.")
        return
    
    # Check if source account has sufficient balance
    try:
        source_public_key = config.get_source_public_key()
        sufficient, current_balance, error_msg = client.check_sufficient_balance(source_public_key, amount)
        
        if not sufficient:
            print(f"❌ Insufficient balance: {error_msg}")
            return
        else:
            print(f"💰 Source balance: {current_balance} XLM")
    except Exception as e:
        print(f"⚠️  Warning: Could not verify balance: {e}")
    
    confirm = input(f"Create new account with {amount} XLM starting balance? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Account creation cancelled.")
        return
    
    try:
        new_public_key, new_secret_key = client.create_account(config.source_secret, amount)
        print("✅ Account created successfully!")
        print(f"🔑 Public Key: {new_public_key}")
        print(f"🔐 Secret Key: {new_secret_key}")
        print("⚠️  IMPORTANT: Save your secret key securely! It cannot be recovered.")
    except Exception as e:
        print(f"❌ Account creation failed: {e}")

def check_account_balance(client):
    """Check account balance."""
    print("\n--- Check Account Balance ---")
    account_id = input("Enter account public key (leave empty for source account): ").strip()
    
    if not account_id:
        try:
            account_id = config.get_source_public_key()
            print(f"Using source account: {account_id}")
        except Exception as e:
            print(f"❌ Error getting source account: {e}")
            return
    
    if not is_valid_stellar_address(account_id):
        print("❌ Invalid Stellar address.")
        return
    
    try:
        balance, exists = client.get_account_balance(account_id)
        if not exists:
            print("❌ Account not found or not funded.")
            return
        
        print(f"💰 Account Balance: {balance} XLM")
    except Exception as e:
        print(f"❌ Error checking balance: {e}")

def check_transaction_status(client):
    """Check transaction status."""
    print("\n--- Check Transaction Status ---")
    tx_hash = input("Enter transaction hash: ").strip()
    
    if not tx_hash:
        print("❌ Transaction hash cannot be empty.")
        return
    
    if len(tx_hash) < 10:
        print("❌ Invalid transaction hash.")
        return
    
    try:
        tx_details = client.get_transaction_status(tx_hash)
        print("✅ Transaction Details:")
        print(f"Hash: {tx_details.get('hash', 'N/A')}")
        print(f"Ledger: {tx_details.get('ledger', 'N/A')}")
        print(f"Successful: {tx_details.get('successful', 'N/A')}")
        print(f"Created: {tx_details.get('created_at', 'N/A')}")
        print(f"Fee Paid: {tx_details.get('fee_paid', 'N/A')} stroops")
        
        if tx_details.get('successful'):
            print("🎉 Transaction was successful!")
        else:
            print("❌ Transaction failed!")
            if 'result_xdr' in tx_details:
                print(f"Result: {tx_details['result_xdr']}")
    except Exception as e:
        print(f"❌ Error checking transaction status: {e}")

def show_account_details(client):
    """Show detailed account information."""
    print("\n--- Account Details ---")
    account_id = input("Enter account public key (leave empty for source account): ").strip()
    
    if not account_id:
        try:
            account_id = config.get_source_public_key()
            print(f"Using source account: {account_id}")
        except Exception as e:
            print(f"❌ Error getting source account: {e}")
            return
    
    if not is_valid_stellar_address(account_id):
        print("❌ Invalid Stellar address.")
        return
    
    try:
        details = client.get_account_balance_detailed(account_id)
        print(f"\n📋 Account Details for: {details['account_id']}")
        print("-" * 60)
        print(f"Sequence: {details['sequence']}")
        print(f"Subentries: {details['num_subentries']}")
        print(f"Thresholds: {details['thresholds']}")
        print(f"Flags: {details['flags']}")
        print("\n💰 Balances:")
        for balance in details['balances']:
            print(f"  Asset: {balance['asset_code']} ({balance['asset_type']})")
            print(f"  Total: {balance['balance']}")
            print(f"  Available: {balance['available']}")
            if balance.get('limit'):
                print(f"  Limit: {balance['limit']}")
            print("-" * 40)
    except Exception as e:
        print(f"❌ Error fetching account details: {e}")

def prompt_and_send():
    """Interactive CLI with menu system for Stellar Agent."""
    client = StellarClient()
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please set SOURCE_SECRET in your environment variables or .env file")
        return
    
    while True:
        show_main_menu()
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            send_payment(client)
        elif choice == '2':
            view_transaction_history(client)
        elif choice == '3':
            create_new_account(client)
        elif choice == '4':
            check_account_balance(client)
        elif choice == '5':
            check_transaction_status(client)
        elif choice == '6':
            show_account_details(client)
        elif choice == '7':
            print("👋 Thank you for using Stellar Agent!")
            break
        else:
            print("❌ Invalid choice. Please enter a number between 1-7.")
        
        input("\nPress Enter to continue...")

def run():
    """Entry point for the CLI."""
    prompt_and_send()
