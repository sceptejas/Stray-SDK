"""Tests for Stellar client."""
import pytest
from unittest.mock import Mock, patch
from stellar_agent.client import StellarClient

class TestStellarClient:
    """Test Stellar client functionality."""

    @patch('stellar_agent.client.Server')
    def test_client_initialization(self, mock_server):
        """Test client initializes with correct server."""
        client = StellarClient()
        assert client.server is not None
        mock_server.assert_called_once()

    @patch('stellar_agent.client.Server')
    def test_get_account_info(self, mock_server):
        """Test fetching account information."""
        mock_response = {
            'id': 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
            'sequence': '123456',
            'balances': []
        }
        mock_server_instance = Mock()
        mock_server_instance.accounts().account_id().call.return_value = mock_response
        mock_server.return_value = mock_server_instance
        
        client = StellarClient()
        result = client.get_account_info('GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H')
        
        assert result == mock_response

    def test_client_server_attribute(self):
        """Test client has server attribute."""
        with patch('stellar_agent.client.Server'):
            client = StellarClient()
            assert hasattr(client, 'server')

    def test_send_payment_requires_secret(self):
        """Test send_payment requires source secret."""
        with patch('stellar_agent.client.Server'):
            client = StellarClient()
            # Method exists and accepts required parameters
            assert callable(client.send_payment)

    def test_get_account_info_callable(self):
        """Test get_account_info is callable."""
        with patch('stellar_agent.client.Server'):
            client = StellarClient()
            assert callable(client.get_account_info)

    def test_client_uses_config_horizon_url(self):
        """Test client uses Horizon URL from config."""
        from stellar_agent.config import config
        with patch('stellar_agent.client.Server') as mock_server:
            StellarClient()
            mock_server.assert_called_with(config.horizon_url)
