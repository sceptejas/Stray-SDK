"""Example: Send multiple payments using Stray SDK."""
from dotenv import load_dotenv
from stellar_agent.client import StellarClient
from stellar_agent.config import config
from stellar_agent.utils.validators import is_valid_stellar_address, is_valid_amount

# Load environment variables
load_dotenv()

def main():
    """Send batch payments example."""
    print("=== Stray SDK: Batch Payments Example ===\n")
    
    # Initialize client
    client = StellarClient()
    
    # List of payments to send
    payments = [
        {
            "destination": "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            "amount": 5.0,
            "memo": "Payment 1"
        },
        {
            "destination": "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            "amount": 3.0,
            "memo": "Payment 2"
        },
    ]
    
    try:
        config.validate()
        
        print(f"Processing {len(payments)} payments...\n")
        
        for i, payment in enumerate(payments, 1):
            dest = payment['destination']
            amt = payment['amount']
            memo = payment.get('memo', '')
            
            # Validate
            if not is_valid_stellar_address(dest):
                print(f"❌ Payment {i}: Invalid address")
                continue
            
            if not is_valid_amount(amt):
                print(f"❌ Payment {i}: Invalid amount")
                continue
            
            print(f"Payment {i}: {amt} XLM → {dest[:8]}... ({memo})")
            
            try:
                response = client.send_payment(
                    source_secret=config.source_secret,
                    destination_public=dest,
                    amount=amt
                )
                print(f"  ✅ Success! Hash: {response['hash'][:16]}...\n")
            except Exception as e:
                print(f"  ❌ Failed: {e}\n")
                
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")

if __name__ == "__main__":
    main()
