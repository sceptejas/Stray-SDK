"""Stellar blockchain client for payment operations."""
from stellar_sdk import Server, Keypair, TransactionBuilder, Asset
from stellar_sdk.operation import Payment
from stellar_sdk.exceptions import (
    NotFoundError, BadResponseError, NetworkError, 
    Ed25519SecretSeedInvalidError
)
from typing import Dict, Any
from .config import config

class StellarClient:
    """Client for interacting with Stellar blockchain."""
    
    def __init__(self):
        self.server = Server(config.horizon_url)
    
    def get_account_info(self, account_id: str) -> Dict[str, Any]:
        """
        Fetch account information from Horizon.
        
        Args:
            account_id: Public key of the account
            
        Returns:
            Account information dictionary
            
        Raises:
            RuntimeError: With descriptive message about what failed
        """
        try:
            response = self.server.accounts().account_id(account_id).call()
            return response
        except NotFoundError:
            raise RuntimeError(
                f"Account not found: {account_id}. "
                "Check that the public key is correct and the account exists on the network. "
                "For testnet, you may need to fund the account first using the Stellar Laboratory."
            )
        except (BadResponseError, NetworkError) as e:
            raise RuntimeError(
                f"Network error while fetching account info: {str(e)}. "
                "Check your internet connectivity and try again. "
                f"Horizon URL: {config.horizon_url}"
            )
    
    def send_payment(
        self, 
        source_secret: str, 
        destination_public: str, 
        amount: float
    ) -> Dict[str, Any]:
        """
        Send XLM payment to a destination address.
        
        Args:
            source_secret: Secret key of the source account
            destination_public: Public key of the destination account
            amount: Amount of XLM to send
            
        Returns:
            Transaction response dictionary
            
        Raises:
            RuntimeError: With descriptive message about what failed
        """
        try:
            source_keypair = Keypair.from_secret(source_secret)
        except Ed25519SecretSeedInvalidError:
            raise RuntimeError(
                "Invalid source secret key format. "
                "Check that SOURCE_SECRET is set correctly in your environment variables. "
                "Secret keys should start with 'S' and be 56 characters long."
            )
        
        try:
            source_account = self.server.load_account(source_keypair.public_key)
        except NotFoundError:
            raise RuntimeError(
                f"Source account not found: {source_keypair.public_key}. "
                "Check that your account exists on the network and has been funded. "
                "For testnet, use the Stellar Laboratory to create and fund your account."
            )
        except (BadResponseError, NetworkError) as e:
            raise RuntimeError(
                f"Network error while loading source account: {str(e)}. "
                "Check your internet connectivity and try again. "
                f"Horizon URL: {config.horizon_url}"
            )

        try:
            transaction = (
                TransactionBuilder(
                    source_account=source_account,
                    network_passphrase=config.network_passphrase,
                    base_fee=100,
                )
                .append_operation(
                    Payment(
                        destination=destination_public,
                        asset=Asset.native(),
                        amount=str(amount)
                    )
                )
                .set_timeout(30)
                .build()
            )

            transaction.sign(source_keypair)
            response = self.server.submit_transaction(transaction)
            return response
            
        except NotFoundError:
            raise RuntimeError(
                f"Destination account not found: {destination_public}. "
                "Check that the destination public key is correct and the account exists. "
                "The recipient may need to create their account first."
            )
        except BadResponseError as e:
            error_msg = str(e)
            if "insufficient balance" in error_msg.lower():
                raise RuntimeError(
                    f"Insufficient balance to send {amount} XLM. "
                    "Check your account balance and ensure you have enough XLM for the "
                    "payment plus transaction fees (minimum ~0.00001 XLM per operation)."
                )
            elif "destination account does not exist" in error_msg.lower():
                raise RuntimeError(
                    f"Destination account does not exist: {destination_public}. "
                    "The recipient needs to create and fund their account first."
                )
            else:
                raise RuntimeError(
                    f"Transaction rejected by network: {error_msg}. "
                    "Check account balances, network status, and transaction parameters."
                )
        except NetworkError as e:
            raise RuntimeError(
                f"Network connection failed: {str(e)}. "
                "Check your internet connectivity and try again. "
                f"Horizon URL: {config.horizon_url}"
            )
