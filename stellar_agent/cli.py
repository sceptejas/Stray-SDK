"""Command-line interface for Stellar Agent."""
from .client import StellarClient
from .config import config
from .utils.validators import is_valid_stellar_address, is_valid_amount


def show_menu() -> str:
    """Display main menu and return user choice."""
    print("\n--- Stellar Agent ---")
    print("1. Send XLM payment")
    print("2. Check account balance")
    print("3. View transaction history")
    print("4. Exit")
    return input("Choose an option (1-4): ").strip()


def cmd_send_payment(client: StellarClient) -> None:
    """Handle interactive send-payment flow."""
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

    print(f"Sending {amount} XLM to {destination}...")
    try:
        response = client.send_payment(config.source_secret, destination, amount)
        print("✅ Transaction Successful!")
        print("Transaction Hash:", response["hash"])
    except Exception as e:
        print("❌ Transaction Failed:", str(e))


def cmd_check_balance(client: StellarClient) -> None:
    """Handle interactive balance-check flow."""
    account_id = input(
        "Enter account public key (leave blank to use configured account): "
    ).strip()

    if not account_id:
        if not config.monitor_account_id:
            print("❌ No account configured. Set MONITOR_ACCOUNT_ID in your .env file.")
            return
        account_id = config.monitor_account_id

    if not is_valid_stellar_address(account_id):
        print("❌ Invalid Stellar address.")
        return

    try:
        balances = client.get_balance(account_id)
        print(f"\n💰 Balances for {account_id[:8]}...{account_id[-4:]}:")
        for b in balances:
            print(f"  {b['asset']:>10}: {b['balance']}")
    except Exception as e:
        print("❌ Failed to fetch balance:", str(e))


def cmd_transaction_history(client: StellarClient) -> None:
    """Handle interactive transaction-history flow."""
    account_id = input(
        "Enter account public key (leave blank to use configured account): "
    ).strip()

    if not account_id:
        if not config.monitor_account_id:
            print("❌ No account configured. Set MONITOR_ACCOUNT_ID in your .env file.")
            return
        account_id = config.monitor_account_id

    if not is_valid_stellar_address(account_id):
        print("❌ Invalid Stellar address.")
        return

    limit_str = input("How many transactions to show? (default 10): ").strip()
    try:
        limit = int(limit_str) if limit_str else 10
    except ValueError:
        limit = 10

    try:
        txs = client.get_transaction_history(account_id, limit=limit)
        if not txs:
            print("ℹ️  No transactions found for this account.")
            return

        print(f"\n📜 Last {len(txs)} transaction(s) for {account_id[:8]}...{account_id[-4:]}:")
        for i, tx in enumerate(txs, 1):
            status = "✅" if tx["successful"] else "❌"
            print(
                f"  {i:>2}. {status} {tx['created_at']}  "
                f"ops={tx['operation_count']}  "
                f"fee={tx['fee_charged']}  "
                f"hash={tx['hash'][:12]}..."
            )
    except Exception as e:
        print("❌ Failed to fetch transaction history:", str(e))


def prompt_and_send():
    """Interactive CLI menu for Stellar Agent."""
    client = StellarClient()

    try:
        config.validate()
    except ValueError as e:
        print(f"⚠️  Configuration Warning: {e}")
        print("Some features (e.g. sending payments) may be unavailable.\n")

    while True:
        choice = show_menu()

        if choice == "1":
            cmd_send_payment(client)
        elif choice == "2":
            cmd_check_balance(client)
        elif choice == "3":
            cmd_transaction_history(client)
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please choose 1-4.")


def run():
    """Entry point for the CLI."""
    prompt_and_send()
