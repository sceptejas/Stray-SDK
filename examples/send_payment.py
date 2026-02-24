"""Example: Send XLM payment using Stray SDK."""
import os
from dotenv import load_dotenv
from stellar_agent.client import StellarClient
from stellar_agent.config import config

# Load environment variables
load_dotenv()

def main():
    """Send a payment example."""
    print("=== Stray SDK: Send Payment Example ===\n")
    
    # Initialize client
    client = StellarClient()
    
    # Example payment details
    destination = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
    amount = 10.0
    
    print(f"Sending {amount} XLM to {destination}...")
    
    try:
        # Validate config
        config.validate()
        
        # Send payment
        response = client.send_payment(
            source_secret=config.source_secret,
            destination_public=destination,
            amount=amount
        )
        
        print("\n✅ Payment Successful!")
        print(f"Transaction Hash: {response['hash']}")
        print(f"Ledger: {response.get('ledger', 'N/A')}")
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("Set SOURCE_SECRET in your .env file")
    except Exception as e:
        print(f"\n❌ Transaction Failed: {e}")

if __name__ == "__main__":
    main()
