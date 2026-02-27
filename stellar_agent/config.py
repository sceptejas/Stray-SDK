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
    
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not self.source_secret:
            raise ValueError("SOURCE_SECRET is required in environment variables")
        return True

# Global config instance
config = Config()
