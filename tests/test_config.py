"""Tests for configuration management."""
import pytest
import os
from stellar_agent.config import Config

class TestConfig:
    """Test configuration class."""

    def test_default_horizon_url(self):
        """Test default Horizon URL for testnet."""
        config = Config()
        assert config.horizon_url == "https://horizon-testnet.stellar.org"

    def test_default_network_passphrase(self):
        """Test default network passphrase."""
        config = Config()
        assert config.network_passphrase == "Test SDF Network ; September 2015"

    def test_environment_variable_override(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("HORIZON_URL", "https://custom-horizon.org")
        config = Config()
        assert config.horizon_url == "https://custom-horizon.org"

    def test_validate_missing_source_secret(self):
        """Test validation fails without source secret."""
        config = Config()
        config.source_secret = ""
        with pytest.raises(ValueError, match="SOURCE_SECRET is required"):
            config.validate()

    def test_validate_with_source_secret(self, monkeypatch):
        """Test validation passes with source secret."""
        monkeypatch.setenv("SOURCE_SECRET", "STEST123")
        config = Config()
        assert config.validate() is True
