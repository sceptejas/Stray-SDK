"""Configuration management for Stellar Agent."""

from decimal import Decimal, InvalidOperation
import os
from typing import Dict, Optional

from dotenv import find_dotenv, load_dotenv
from stellar_sdk import Keypair
from stellar_sdk.strkey import StrKey

DEFAULT_NETWORKS: Dict[str, Dict[str, str]] = {
    "testnet": {
        "horizon_url": "https://horizon-testnet.stellar.org",
        "network_passphrase": "Test SDF Network ; September 2015",
    },
    "mainnet": {
        "horizon_url": "https://horizon.stellar.org",
        "network_passphrase": "Public Global Stellar Network ; September 2015",
    },
}

TRUTHY_VALUES = {"1", "true", "yes", "on"}
FALSY_VALUES = {"0", "false", "no", "off"}


def _load_environment() -> None:
    """Load environment variables from the nearest .env file when present."""
    dotenv_path = find_dotenv(filename=".env", usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)


def _clean_env(name: str, default: str = "") -> str:
    """Read a stripped environment variable value."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def _parse_boolean(name: str, default: bool) -> bool:
    """Parse a boolean environment variable with explicit accepted values."""
    raw_value = _clean_env(name)
    if raw_value == "":
        return default

    normalized = raw_value.lower()
    if normalized in TRUTHY_VALUES:
        return True
    if normalized in FALSY_VALUES:
        return False

    allowed_values = ", ".join(sorted(TRUTHY_VALUES | FALSY_VALUES))
    raise ValueError(f"{name} must be one of: {allowed_values}")


def _parse_decimal(name: str, default: str) -> Decimal:
    """Parse a decimal environment variable."""
    raw_value = _clean_env(name, default)
    try:
        return Decimal(raw_value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a valid decimal number") from exc


def _resolve_network_defaults(network_name: str) -> Dict[str, str]:
    """Get default Horizon settings for the selected network."""
    normalized = network_name.lower().strip()
    if normalized not in DEFAULT_NETWORKS:
        allowed = ", ".join(sorted(DEFAULT_NETWORKS))
        raise ValueError(f"STELLAR_NETWORK must be one of: {allowed}")
    return DEFAULT_NETWORKS[normalized]


class Config:
    """Configuration class for Stellar Agent."""

    def __init__(self):
        _load_environment()
        self.reload()

    def reload(self) -> None:
        """Reload configuration from environment variables."""
        network_name = _clean_env("STELLAR_NETWORK", "testnet")
        network_defaults = _resolve_network_defaults(network_name)

        self.stellar_network = network_name.lower()
        self.horizon_url = _clean_env(
            "HORIZON_URL", network_defaults["horizon_url"]
        )
        self.network_passphrase = _clean_env(
            "NETWORK_PASSPHRASE", network_defaults["network_passphrase"]
        )
        self.source_secret = _clean_env("SOURCE_SECRET")
        self.monitor_account_id = _clean_env("MONITOR_ACCOUNT_ID")
        self.destination_account_id = _clean_env("DESTINATION_ACCOUNT_ID")
        self.minimum_balance_xlm = _parse_decimal("MINIMUM_BALANCE_XLM", "1.0")
        self.balance_check_enabled = _parse_boolean(
            "BALANCE_CHECK_ENABLED", True
        )

    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not self.source_secret:
            raise ValueError("SOURCE_SECRET is required in environment variables")

        if not StrKey.is_valid_ed25519_secret_seed(self.source_secret):
            raise ValueError(
                "SOURCE_SECRET must be a valid Stellar secret seed"
            )

        if not self.horizon_url:
            raise ValueError("HORIZON_URL cannot be empty")

        if not self.network_passphrase:
            raise ValueError("NETWORK_PASSPHRASE cannot be empty")

        if self.minimum_balance_xlm < 0:
            raise ValueError("MINIMUM_BALANCE_XLM cannot be negative")

        self._validate_optional_account(
            "MONITOR_ACCOUNT_ID", self.monitor_account_id
        )
        self._validate_optional_account(
            "DESTINATION_ACCOUNT_ID", self.destination_account_id
        )

        return True

    def _validate_optional_account(self, name: str, account_id: str) -> None:
        """Validate optional account IDs when they are configured."""
        if account_id and not StrKey.is_valid_ed25519_public_key(account_id):
            raise ValueError(f"{name} must be a valid Stellar public key")

    def get_source_public_key(self) -> str:
        """Get the public key corresponding to the source secret."""
        try:
            keypair = Keypair.from_secret(self.source_secret)
            return keypair.public_key
        except Exception as exc:
            raise ValueError(f"Invalid SOURCE_SECRET: {exc}") from exc


config = Config()
