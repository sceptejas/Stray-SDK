"""Command-line interface for Stellar Agent."""
from .client import StellarClient
from .config import config
from .utils.validators import is_valid_stellar_address, is_valid_amount

def prompt_and_send():
    """Interactive CLI for sending Stellar payments."""
    client = StellarClient()
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("💡 Please set SOURCE_SECRET in your environment variables or .env file")
        print("   Example: export SOURCE_SECRET=SABC123...")
        return
    
    while True:
        print("\n--- Stellar Agent ---")
        destination = input("Enter destination public key (or type 'exit' to quit): ").strip()
        
        if destination.lower() == "exit":
            break
        
        # Validate destination address using enhanced validation
        if not is_valid_stellar_address(destination):
            print("❌ Invalid Stellar public key.")
            print("💡 Public keys must:")
            print("   • Start with 'G'")
            print("   • Be exactly 56 characters long")
            print("   • Use valid Base32 encoding (A-Z, 2-7)")
            print("   • Pass cryptographic validation")
            print("   Example: GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H")
            continue
        
        amount_str = input("Enter amount to send (in XLM): ").strip()
        
        try:
            amount = float(amount_str)
            if not is_valid_amount(amount):
                print("❌ Amount must be positive.")
                print("💡 Enter a number greater than 0 (e.g., 10.5)")
                continue
        except ValueError:
            print("❌ Invalid amount format.")
            print("💡 Please enter a valid number (e.g., 10.5 or 0.001)")
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
            print(f"   Transaction Hash: {response['hash']}")
            print("💡 You can view this transaction on the Stellar Explorer")
        except RuntimeError as e:
            # RuntimeError contains our descriptive error messages
            print(f"❌ Transaction Failed: {e}")
        except Exception as e:
            # Fallback for unexpected errors
            print(f"❌ Unexpected error: {str(e)}")
            print("💡 If this persists, check network connectivity and configuration")
            print("Transaction Hash:", response['hash'])
            if 'ledger' in response:
                print("Ledger:", response['ledger'])
        except RuntimeError as e:
            print(f"❌ Transaction Failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("💡 Please check your network connectivity and configuration.")

def run():
    """Entry point for the CLI."""
    prompt_and_send()
