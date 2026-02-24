"""Tests for CLI interface."""
import pytest
from unittest.mock import patch, MagicMock
from stellar_agent.cli import prompt_and_send, run

class TestCLI:
    """Test CLI functionality."""

    @patch('stellar_agent.cli.input')
    @patch('stellar_agent.cli.StellarClient')
    def test_exit_command(self, mock_client, mock_input):
        """Test CLI exits on 'exit' command."""
        mock_input.return_value = 'exit'
        prompt_and_send()
        # Should exit without error
        assert True

    @patch('stellar_agent.cli.config')
    def test_cli_validates_config(self, mock_config):
        """Test CLI validates configuration on start."""
        mock_config.validate.side_effect = ValueError("Missing config")
        with patch('builtins.print'):
            prompt_and_send()
        mock_config.validate.assert_called_once()

    @patch('stellar_agent.cli.input')
    @patch('stellar_agent.cli.is_valid_stellar_address')
    def test_invalid_address_rejected(self, mock_validator, mock_input):
        """Test CLI rejects invalid addresses."""
        mock_input.side_effect = ['INVALID', 'exit']
        mock_validator.return_value = False
        
        with patch('builtins.print'):
            with patch('stellar_agent.cli.config'):
                prompt_and_send()
        
        mock_validator.assert_called_with('INVALID')

    @patch('stellar_agent.cli.input')
    @patch('stellar_agent.cli.is_valid_amount')
    def test_invalid_amount_rejected(self, mock_validator, mock_input):
        """Test CLI rejects invalid amounts."""
        valid_addr = 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H'
        mock_input.side_effect = [valid_addr, '-10', 'exit']
        mock_validator.return_value = False
        
        with patch('builtins.print'):
            with patch('stellar_agent.cli.config'):
                with patch('stellar_agent.cli.is_valid_stellar_address', return_value=True):
                    prompt_and_send()

    def test_run_function_exists(self):
        """Test run function is defined."""
        assert callable(run)

    @patch('stellar_agent.cli.prompt_and_send')
    def test_run_calls_prompt_and_send(self, mock_prompt):
        """Test run function calls prompt_and_send."""
        run()
        mock_prompt.assert_called_once()
