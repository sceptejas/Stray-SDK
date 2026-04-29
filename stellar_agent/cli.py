"""Command-line interface for Stellar Agent."""
from .client import StellarClient
from .config import config
from .utils.validators import is_valid_stellar_address, is_valid_amount
from .multisig import MultiSigClient


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


def multisig_send():
    """
    Interactive CLI for building and submitting multi-signature XLM payments.

    Workflow
    --------
    1. Collect destination, amount, and optional text memo.
    2. Collect one or more co-signer secret keys (in addition to the source
       key stored in SOURCE_SECRET).
    3. Build a signed transaction envelope (XDR).
    4. Optionally display the XDR so it can be passed to offline signers.
    5. Submit the transaction to the Stellar network.

    The source account **must already have multisig thresholds configured**
    on-chain.  Use the ``configure-multisig`` sub-command (or call
    ``MultiSigClient.configure_multisig_account()`` directly) to set up the
    account before using this command.
    """
    # Validate base configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please set SOURCE_SECRET in your environment variables or .env file")
        return

    client = MultiSigClient()

    print("\n--- Stellar Agent · Multi-Sig Payment ---")
    print("ℹ️  Your source account (SOURCE_SECRET) must already have multisig")
    print("   thresholds configured. See the README for details.\n")

    # ------------------------------------------------------------------
    # Collect destination
    # ------------------------------------------------------------------
    while True:
        destination = input("Enter destination public key (or 'exit' to quit): ").strip()
        if destination.lower() == "exit":
            return
        if is_valid_stellar_address(destination):
            break
        print("❌ Invalid Stellar address. Must start with 'G' and be 56 characters.")

    # ------------------------------------------------------------------
    # Collect amount
    # ------------------------------------------------------------------
    while True:
        amount_str = input("Enter amount to send (in XLM): ").strip()
        try:
            amount = float(amount_str)
            if is_valid_amount(amount):
                break
            print("❌ Amount must be positive.")
        except ValueError:
            print("❌ Invalid amount. Please enter a number.")

    # ------------------------------------------------------------------
    # Optional memo
    # ------------------------------------------------------------------
    memo = input("Enter an optional memo (press Enter to skip): ").strip()

    # ------------------------------------------------------------------
    # Collect co-signer secrets
    # ------------------------------------------------------------------
    print("\nEnter co-signer secret keys one at a time.")
    print("Press Enter with no input when done.\n")

    co_signer_secrets = []
    idx = 1
    while True:
        secret = input(f"Co-signer {idx} secret key (or Enter to finish): ").strip()
        if not secret:
            break
        if not (len(secret) == 56 and secret.startswith("S")):
            print("❌ Invalid secret key format. Must start with 'S' and be 56 characters.")
            continue
        co_signer_secrets.append(secret)
        idx += 1

    # ------------------------------------------------------------------
    # Build transaction envelope
    # ------------------------------------------------------------------
    print(f"\n🔨 Building multi-sig transaction: {amount} XLM → {destination} ...")
    try:
        xdr = client.build_multisig_payment(
            source_secret=config.source_secret,
            destination_public=destination,
            amount=amount,
            signers=co_signer_secrets if co_signer_secrets else None,
            memo=memo,
        )
    except (ValueError, RuntimeError) as e:
        print(f"❌ Failed to build transaction: {e}")
        return

    sig_count = client.count_signatures(xdr)
    print(f"✅ Transaction built with {sig_count} signature(s).")

    # ------------------------------------------------------------------
    # Optionally display XDR (for out-of-band signing)
    # ------------------------------------------------------------------
    show_xdr = input("\nShow XDR for additional offline signing? (y/N): ").strip().lower()
    if show_xdr == "y":
        print("\n--- Transaction XDR (copy and share with remaining signers) ---")
        print(xdr)
        print("---\n")

        updated_xdr = input(
            "Paste updated XDR after additional signing (or press Enter to use current): "
        ).strip()
        if updated_xdr:
            xdr = updated_xdr
            try:
                sig_count = client.count_signatures(xdr)
                print(f"ℹ️  Updated XDR has {sig_count} signature(s).")
            except ValueError as e:
                print(f"❌ Invalid XDR provided: {e}")
                return

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------
    confirm = input(f"\nSubmit transaction with {sig_count} signature(s)? (y/N): ").strip().lower()
    if confirm != "y":
        print("Transaction cancelled.")
        return

    try:
        response = client.submit_transaction(xdr)
        print("✅ Multi-Sig Transaction Successful!")
        print("Transaction Hash:", response.get("hash", "N/A"))
        if "ledger" in response:
            print("Ledger:", response["ledger"])
    except (ValueError, RuntimeError) as e:
        print(f"❌ Submission Failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Please check your network connectivity and configuration.")


def run():
    """Entry point for the CLI — prompts the user to choose a payment mode."""
    print("╔══════════════════════════════════╗")
    print("║       Stellar Agent CLI          ║")
    print("╚══════════════════════════════════╝")
    print("1. Standard payment (single signature)")
    print("2. Multi-signature payment")
    print("3. Exit")

    while True:
        choice = input("\nSelect mode [1/2/3]: ").strip()
        if choice == "1":
            prompt_and_send()
            break
        elif choice == "2":
            multisig_send()
            break
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")
