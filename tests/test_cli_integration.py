"""Integration smoke tests for CLI functionality."""
import pytest
from unittest.mock import patch, Mock
from stellar_agent.cli import prompt_and_send
from stellar_agent.config import config

class TestCLIIntegration:
    """Test CLI integration scenarios."""
    
    @patch('builtins.input')
    @patch('stellar_agent.cli.StellarClient')
    @patch.object(config, 'validate')
    @patch.object(config, 'get_source_public_key')
    @patch.dict('os.environ', {
        'SOURCE_SECRET': 'SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
        'HORIZON_URL': 'https://horizon-testnet.stellar.org',
        'NETWORK_PASSPHRASE': 'Test SDF Network ; September 2015',
        'BALANCE_CHECK_ENABLED': 'true'
    })
    def test_cli_balance_check_integration(self, mock_get_public_key, mock_validate, mock_client_class, mock_input):
        """Test CLI with balance checking enabled."""
        # Setup mocks
        mock_validate.return_value = True
        mock_get_public_key.return_value = 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H'
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock balance check success
        mock_client.check_sufficient_balance.return_value = (True, 100.0, "")
        mock_client.send_payment.return_value = {'hash': 'test_hash', 'ledger': 12345}
        
        # Mock user inputs
        mock_input.side_effect = [
            'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',  # destination
            '10.5',  # amount
            'exit'   # exit command
        ]
        
        # Run CLI
        with patch('builtins.print') as mock_print:
            prompt_and_send()
        
        # Verify balance check was called
        mock_client.check_sufficient_balance.assert_called_once()
        
        # Verify payment was sent
        mock_client.send_payment.assert_called_once_with(
            config.source_secret,
            'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
            10.5
        )
        
        # Verify success message was printed
        success_printed = any("✅ Transaction Successful!" in str(call) for call in mock_print.call_args_list)
        assert success_printed, "Success message should be printed"
        
    @patch('builtins.input')
    @patch('stellar_agent.cli.StellarClient')
    @patch.object(config, 'validate')
    @patch.object(config, 'get_source_public_key')
    @patch.dict('os.environ', {
        'SOURCE_SECRET': 'SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
        'BALANCE_CHECK_ENABLED': 'true'
    })
    def test_cli_insufficient_balance_scenario(self, mock_get_public_key, mock_validate, mock_client_class, mock_input):
        """Test CLI behavior with insufficient balance."""
        # Setup mocks
        mock_validate.return_value = True
        mock_get_public_key.return_value = 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H'
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock insufficient balance
        mock_client.check_sufficient_balance.return_value = (
            False, 
            5.0, 
            "Insufficient balance. Required: 11.00001 XLM, Available: 5.0 XLM"
        )
        
        # Mock user inputs
        mock_input.side_effect = [
            'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',  # destination
            '10.5',  # amount (more than available)
            'exit'   # exit command
        ]
        
        # Run CLI
        with patch('builtins.print') as mock_print:
            prompt_and_send()
        
        # Verify balance check was called
        mock_client.check_sufficient_balance.assert_called_once()
        
        # Verify payment was NOT sent (insufficient balance)
        mock_client.send_payment.assert_not_called()
        
        # Verify error message was printed
        error_printed = any("❌ Insufficient balance" in str(call) for call in mock_print.call_args_list)
        assert error_printed, "Insufficient balance error should be printed"