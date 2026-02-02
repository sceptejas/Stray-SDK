"""Configuration management for Stellar Agent."""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for Stellar Agent."""
    
    def __init__(self):
        self.horizon_url = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org")
        self.network_passphrase = os.getenv(
            "NETWORK_PASSPHRASE", 
            "Test SDF Network ; September 2015"
        )
        self.source_secret = os.getenv("SOURCE_SECRET", "")
        self.monitor_account_id = os.getenv("MONITOR_ACCOUNT_ID", "")
        self.destination_account_id = os.getenv("DESTINATION_ACCOUNT_ID", "")
        # Balance safety settings
        self.minimum_balance_xlm = float(os.getenv("MINIMUM_BALANCE_XLM", "1.0"))
        self.balance_check_enabled = os.getenv("BALANCE_CHECK_ENABLED", "true").lower() == "true"
    
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not self.source_secret:
            raise ValueError("SOURCE_SECRET is required in environment variables")
        
        # Validate SOURCE_SECRET format
        if len(self.source_secret) != 56 or not self.source_secret.startswith('S'):
            raise ValueError("SOURCE_SECRET must be a valid Stellar secret key (56 characters starting with 'S')")
        
        # Validate network settings
        if not self.horizon_url:
            raise ValueError("HORIZON_URL cannot be empty")
        
        if not self.network_passphrase:
            raise ValueError("NETWORK_PASSPHRASE cannot be empty")
        
        return True
    
    def get_source_public_key(self) -> str:
        """Get the public key corresponding to the source secret."""
        from stellar_sdk import Keypair
        try:
            keypair = Keypair.from_secret(self.source_secret)
            return keypair.public_key
        except Exception as e:
            raise ValueError(f"Invalid SOURCE_SECRET: {e}")

# Global config instance
config = Config()
