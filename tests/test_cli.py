"""Unit tests for the CLI module."""
import pytest
from unittest.mock import patch, Mock
import io
import sys
from stellar_agent.cli import prompt_and_send

@patch('stellar_agent.cli.config')
@patch('stellar_agent.cli.StellarClient')
def test_prompt_and_send_success(mock_client_class, mock_config, monkeypatch):
    """Test successful payment flow."""
    # Setup mock config
    mock_config.validate.return_value = True
    mock_config.source_secret = "SA..."
    
    # Setup mock client
    mock_client = mock_client_class.return_value
    mock_client.send_payment.return_value = {"hash": "abc123def456"}
    
    # Simulate user inputs
    inputs = iter([
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", # valid dest
        "10.5", # valid amount
        "exit"
    ])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    
    # Capture stdout
    captured_output = io.StringIO()
    monkeypatch.setattr('sys.stdout', captured_output)
    
    # Run the function
    prompt_and_send()
    
    output = captured_output.getvalue()
    
    # Assertions
    mock_client.send_payment.assert_called_once_with(
        "SA...", 
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", 
        10.5
    )
    assert "✅ Transaction Successful!" in output
    assert "Transaction Hash: abc123def456" in output


@patch('stellar_agent.cli.config')
@patch('stellar_agent.cli.StellarClient')
def test_prompt_and_send_invalid_address(mock_client_class, mock_config, monkeypatch):
    """Test handling of invalid destination address."""
    mock_config.validate.return_value = True
    
    inputs = iter([
        "invalid_address",
        "exit"
    ])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    
    captured_output = io.StringIO()
    monkeypatch.setattr('sys.stdout', captured_output)
    
    prompt_and_send()
    
    output = captured_output.getvalue()
    assert "❌ Invalid Stellar address" in output
    # Ensure client wasn't called
    mock_client_class.return_value.send_payment.assert_not_called()


@patch('stellar_agent.cli.config')
@patch('stellar_agent.cli.StellarClient')
def test_prompt_and_send_invalid_amount(mock_client_class, mock_config, monkeypatch):
    """Test handling of invalid decimal/amount entries."""
    mock_config.validate.return_value = True
    
    inputs = iter([
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", # valid
        "-5", # invalid, negative 
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", # valid
        "not_a_number", # invalid string
        "exit"
    ])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    
    captured_output = io.StringIO()
    monkeypatch.setattr('sys.stdout', captured_output)
    
    prompt_and_send()
    
    output = captured_output.getvalue()
    assert "❌ Amount must be positive." in output
    assert "❌ Invalid amount. Please enter a number." in output
    mock_client_class.return_value.send_payment.assert_not_called()

@patch('stellar_agent.cli.config')
def test_prompt_and_send_config_error(mock_config, monkeypatch):
    """Test configuration validation failure."""
    mock_config.validate.side_effect = ValueError("Missing SOURCE_SECRET")
    
    captured_output = io.StringIO()
    monkeypatch.setattr('sys.stdout', captured_output)
    
    prompt_and_send()
    
    output = captured_output.getvalue()
    assert "❌ Configuration Error: Missing SOURCE_SECRET" in output
