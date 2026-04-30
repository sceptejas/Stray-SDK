"""Unit tests for the CLI module."""
import pytest
from unittest.mock import patch, Mock, MagicMock
import io
import sys
from stellar_agent.cli import prompt_and_send
from stellar_agent.utils.validators import is_valid_stellar_address, is_valid_amount

@patch('stellar_agent.cli.config')
@patch('stellar_agent.cli.StellarClient')
def test_prompt_and_send_success(mock_client_class, mock_config, monkeypatch):
    """Test successful payment flow."""
    # Setup mock config
    mock_config.validate.return_value = True
    mock_config.source_secret = "SA..."
    
    # Setup mock client
    mock_client = mock_client_class.return_value
    mock_client.send_payment.return_value = {"hash": "abc123def456", "successful": True}
    
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
def test_prompt_and_send_payment_failure(mock_client_class, mock_config, monkeypatch):
    """Test payment failure handling."""
    # Setup mock config
    mock_config.validate.return_value = True
    mock_config.source_secret = "SA..."
    
    # Setup mock client to raise exception
    mock_client = mock_client_class.return_value
    mock_client.send_payment.side_effect = RuntimeError("Insufficient balance")
    
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
    mock_client.send_payment.assert_called_once()
    assert "❌ Payment Failed:" in output
    assert "Insufficient balance" in output


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
def test_prompt_and_send_multiple_invalid_addresses(mock_client_class, mock_config, monkeypatch):
    """Test handling of multiple invalid addresses before success."""
    mock_config.validate.return_value = True
    mock_client = mock_client_class.return_value
    mock_client.send_payment.return_value = {"hash": "abc123def456", "successful": True}
    
    inputs = iter([
        "invalid_address1",
        "ABRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",  # wrong prefix
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",  # valid
        "10.5",
        "exit"
    ])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    
    captured_output = io.StringIO()
    monkeypatch.setattr('sys.stdout', captured_output)
    
    prompt_and_send()
    
    output = captured_output.getvalue()
    # Should show error messages for invalid addresses
    assert output.count("❌ Invalid Stellar address") >= 2
    # Should eventually succeed
    assert "✅ Transaction Successful!" in output
    mock_client.send_payment.assert_called_once()


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
@patch('stellar_agent.cli.StellarClient')
def test_prompt_and_send_zero_amount(mock_client_class, mock_config, monkeypatch):
    """Test handling of zero amount."""
    mock_config.validate.return_value = True
    
    inputs = iter([
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", # valid
        "0", # zero amount
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", # valid
        "10.5", # valid amount
        "exit"
    ])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    
    captured_output = io.StringIO()
    monkeypatch.setattr('sys.stdout', captured_output)
    
    prompt_and_send()
    
    output = captured_output.getvalue()
    assert "❌ Amount must be positive." in output
    mock_client_class.return_value.send_payment.assert_called_once_with(
        mock_config.source_secret,
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
        10.5
    )

@patch('stellar_agent.cli.config')
def test_prompt_and_send_config_error(mock_config, monkeypatch):
    """Test configuration validation failure."""
    mock_config.validate.side_effect = ValueError("Missing SOURCE_SECRET")
    
    captured_output = io.StringIO()
    monkeypatch.setattr('sys.stdout', captured_output)
    
    prompt_and_send()
    
    output = captured_output.getvalue()
    assert "❌ Configuration Error: Missing SOURCE_SECRET" in output

@patch('stellar_agent.cli.config')
def test_prompt_and_send_keyboard_interrupt(mock_config, monkeypatch):
    """Test handling of keyboard interrupt (Ctrl+C)."""
    mock_config.validate.return_value = True
    
    # Simulate keyboard interrupt during input
    def mock_input_interrupt(prompt):
        raise KeyboardInterrupt()
    
    monkeypatch.setattr('builtins.input', mock_input_interrupt)
    
    captured_output = io.StringIO()
    monkeypatch.setattr('sys.stdout', captured_output)
    
    # Should not raise exception, should handle gracefully
    prompt_and_send()
    
    output = captured_output.getvalue()
    assert "\n" in output  # Should show newline on interrupt

@patch('stellar_agent.cli.config')
@patch('stellar_agent.cli.StellarClient')
def test_prompt_and_send_multiple_transactions(mock_client_class, mock_config, monkeypatch):
    """Test multiple successful transactions in one session."""
    mock_config.validate.return_value = True
    mock_client = mock_client_class.return_value
    mock_client.send_payment.return_value = {"hash": "abc123def456", "successful": True}
    
    inputs = iter([
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", # valid dest
        "10.5", # valid amount
        "GDQPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", # second dest
        "5.0", # second amount
        "exit"
    ])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    
    captured_output = io.StringIO()
    monkeypatch.setattr('sys.stdout', captured_output)
    
    prompt_and_send()
    
    output = captured_output.getvalue()
    
    # Should have made two successful payments
    assert mock_client.send_payment.call_count == 2
    assert output.count("✅ Transaction Successful!") == 2
    
    # Verify the calls were made with correct parameters
    mock_client.send_payment.assert_any_call(
        mock_config.source_secret,
        "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
        10.5
    )
    mock_client.send_payment.assert_any_call(
        mock_config.source_secret,
        "GDQPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
        5.0
    )

# Test validator functions used in CLI
def test_cli_validators_valid():
    """Test validator functions with valid inputs."""
    assert is_valid_stellar_address("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H") is True
    assert is_valid_amount(10.5) is True
    assert is_valid_amount(0.0000001) is True

def test_cli_validators_invalid():
    """Test validator functions with invalid inputs."""
    assert is_valid_stellar_address("invalid") is False
    assert is_valid_amount(0) is False
    assert is_valid_amount(-5) is False
    assert is_valid_stellar_address("") is False
