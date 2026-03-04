"""Command-line interface for Stellar Agent."""
from .client import StellarClient, PaymentError
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
        print("Please set SOURCE_SECRET in your environment variables or .env file")
        return

    while True:
        print("\n--- Stellar Agent ---")
        print("Options:")
        print("  1. Send Payment")
        print("  2. Check Balance")
        print("  3. View Transaction History")
        print("  4. Exit")

        choice = input("\nSelect an option (1-4): ").strip()

        if choice == "4" or choice.lower() == "exit":
            break

        elif choice == "2":
            # Check balance
            account_id = input("Enter account public key (or press Enter for your account): ").strip()
            if not account_id:
                try:
                    from stellar_sdk import Keypair
                    account_id = Keypair.from_secret(config.source_secret).public_key
                except:
                    print("❌ Could not determine your public key.")
                    continue

            if not is_valid_stellar_address(account_id):
                print("❌ Invalid Stellar address.")
                continue

            try:
                balances = client.get_balance(account_id)
                print(f"\n✅ Account Balance for {account_id[:8]}...{account_id[-8:]}:")
                print(f"   XLM: {balances['native']} XLM")
                if balances['assets']:
                    print("   Other Assets:")
                    for asset in balances['assets']:
                        print(f"      {asset['asset_code']}: {asset['balance']}")
            except PaymentError as e:
                print(f"❌ {e}")

        elif choice == "3":
            # View transaction history
            account_id = input("Enter account public key (or press Enter for your account): ").strip()
            if not account_id:
                try:
                    from stellar_sdk import Keypair
                    account_id = Keypair.from_secret(config.source_secret).public_key
                except:
                    print("❌ Could not determine your public key.")
                    continue

            if not is_valid_stellar_address(account_id):
                print("❌ Invalid Stellar address.")
                continue

            try:
                transactions = client.get_transaction_history(account_id, limit=5)
                print(f"\n✅ Recent Transactions for {account_id[:8]}...{account_id[-8:]}:")
                if not transactions:
                    print("   No transactions found.")
                else:
                    for i, tx in enumerate(transactions, 1):
                        print(f"\n   {i}. Hash: {tx['hash'][:16]}...")
                        print(f"      Date: {tx['created_at']}")
                        print(f"      Fee: {tx['fee_charged']} stroops")
                        print(f"      Operations: {tx['operation_count']}")
                        print(f"      Memo: {tx['memo']}")
            except PaymentError as e:
                print(f"❌ {e}")

        elif choice == "1":
            # Send payment
            destination = input("Enter destination public key: ").strip()

            # Validate destination address
            if not is_valid_stellar_address(destination):
                print("❌ Invalid Stellar address. Must be a valid Stellar public key.")
                continue

            amount_str = input("Enter amount to send (in XLM): ").strip()

            try:
                amount = float(amount_str)
                if not is_valid_amount(amount):
                    print("❌ Amount must be positive and follow Stellar's precision rules:")
                    print("   - Minimum: 0.0000001 XLM (1 stroop)")
                    print("   - Maximum precision: 7 decimal places")
                    continue
            except ValueError:
                print("❌ Invalid amount. Please enter a number.")
                continue

            # Prompt for optional memo
            memo_input = input("Enter memo (optional, max 28 chars, press Enter to skip): ").strip()
            memo = memo_input if memo_input else None

            print(f"Sending {amount} XLM to {destination}...")
            try:
                response = client.send_payment(config.source_secret, destination, amount, memo)
                print("✅ Transaction Successful!")
                print("Transaction Hash:", response['hash'])
            except PaymentError as e:
                # Only PaymentError messages are sanitized and safe to print
                print(f"❌ Transaction Failed: {e}")
            except Exception:
                # Silent catch-all prevents leaking SDK internals or account metadata
                print("❌ An unexpected error occurred. Please check your configuration and try again.")

        else:
            print("❌ Invalid option. Please choose 1-4.")

def run():
    """Entry point for the CLI."""
    prompt_and_send()
