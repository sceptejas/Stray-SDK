"""Example: Check account balance using Stray SDK."""
import os
from dotenv import load_dotenv
from stellar_agent.client import StellarClient
from stellar_agent.config import config

# Load environment variables
load_dotenv()

def main():
    """Check account balance example."""
    print("=== Stray SDK: Check Balance Example ===\n")
    
    # Initialize client
    client = StellarClient()
    
    # Get account ID from config or use default
    account_id = config.monitor_account_id or "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
    
    print(f"Checking balance for: {account_id}\n")
    
    try:
        # Get account info
        account_info = client.get_account_info(account_id)
        
        print("✅ Account Found!")
        print(f"Account ID: {account_info['id']}")
        print(f"Sequence: {account_info['sequence']}")
        print("\nBalances:")
        
        for balance in account_info['balances']:
            if balance['asset_type'] == 'native':
                print(f"  XLM: {balance['balance']}")
            else:
                asset_code = balance.get('asset_code', 'Unknown')
                print(f"  {asset_code}: {balance['balance']}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
