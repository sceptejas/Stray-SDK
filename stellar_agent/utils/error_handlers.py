"""Enhanced error handling utilities for Stellar Agent."""
import re
from typing import Dict, Any, Optional
from stellar_sdk.exceptions import (
    NotFoundError, BadRequestError, BadResponseError,
    ConnectionError, TimeoutError
)

class StellarErrorHandler:
    """Enhanced error handling for Stellar operations."""
    
    @staticmethod
    def handle_stellar_error(error: Exception, operation: str = "Stellar operation") -> str:
        """
        Handle Stellar SDK errors and provide user-friendly messages.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation being performed
            
        Returns:
            User-friendly error message
        """
        if isinstance(error, NotFoundError):
            if "account" in str(error).lower():
                return f"Account not found. Please check the account address and ensure it exists on the network."
            elif "transaction" in str(error).lower():
                return f"Transaction not found. Please verify the transaction hash is correct."
            else:
                return f"Resource not found. Please check your input and try again."
        
        elif isinstance(error, BadRequestError):
            error_detail = str(error).lower()
            
            if "insufficient balance" in error_detail:
                return "Insufficient balance. Please ensure you have enough XLM to cover the payment, fees, and minimum reserve."
            elif "destination account does not exist" in error_detail:
                return "Destination account does not exist. The recipient must have an active Stellar account to receive payments."
            elif "invalid amount" in error_detail:
                return "Invalid amount specified. Please enter a positive number with appropriate decimal places."
            elif "fee" in error_detail:
                return "Fee-related error. The transaction fee may be too low or there may be network congestion."
            elif "sequence" in error_detail:
                return "Sequence number error. This can happen if multiple transactions are submitted quickly. Please wait and try again."
            else:
                return f"Invalid request: {error_detail}. Please check your input parameters."
        
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return "Network connection error. Please check your internet connection and try again. If the issue persists, the Stellar network may be experiencing high traffic."
        
        elif isinstance(error, BadResponseError):
            return "Invalid response from Stellar network. This could indicate network issues or server problems. Please try again later."
        
        else:
            # Generic error handling
            error_str = str(error).lower()
            
            if "timeout" in error_str:
                return "Operation timed out. The network may be experiencing high traffic. Please try again."
            elif "network" in error_str:
                return "Network error. Please check your internet connection and the Horizon URL configuration."
            elif "key" in error_str or "secret" in error_str:
                return "Invalid key or secret. Please check your Stellar credentials are correct."
            elif "authentication" in error_str or "auth" in error_str:
                return "Authentication error. Please verify your account credentials and permissions."
            else:
                return f"Unexpected error during {operation}: {error}. Please check your configuration and try again."
    
    @staticmethod
    def get_recovery_suggestions(error_message: str) -> str:
        """
        Get recovery suggestions based on error type.
        
        Args:
            error_message: The error message
            
        Returns:
            Recovery suggestions
        """
        suggestions = []
        
        error_lower = error_message.lower()
        
        if "balance" in error_lower:
            suggestions.extend([
                "Check your account balance",
                "Ensure you have enough XLM for minimum reserve (1 XLM)",
                "Consider reducing the payment amount",
                "Fund your account if it has insufficient balance"
            ])
        
        if "account does not exist" in error_lower:
            suggestions.extend([
                "Create the destination account first",
                "Send at least 1 XLM to create and fund the new account",
                "Verify the destination address is correct"
            ])
        
        if "network" in error_lower or "connection" in error_lower:
            suggestions.extend([
                "Check your internet connection",
                "Verify the Horizon URL is correct",
                "Try again in a few minutes",
                "Check Stellar network status at stellar.expert/explorer/public"
            ])
        
        if "key" in error_lower or "secret" in error_lower:
            suggestions.extend([
                "Verify your secret key is correct",
                "Ensure the secret key starts with 'S' and is 56 characters",
                "Check your .env file configuration"
            ])
        
        if "sequence" in error_lower:
            suggestions.extend([
                "Wait a few seconds and try again",
                "Check if other transactions are pending",
                "Ensure you're not submitting multiple transactions simultaneously"
            ])
        
        if not suggestions:
            suggestions.extend([
                "Check your configuration in .env file",
                "Verify all input parameters are correct",
                "Try again with different parameters",
                "Check Stellar network status"
            ])
        
        return "Recovery suggestions:\n" + "\n".join(f"- {suggestion}" for suggestion in suggestions)

def validate_transaction_params(destination: str, amount: float, source_balance: Optional[float] = None) -> Dict[str, Any]:
    """
    Validate transaction parameters with detailed feedback.
    
    Args:
        destination: Destination address
        amount: Amount to send
        source_balance: Optional source account balance
        
    Returns:
        Dictionary with validation results
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Validate destination address
    if not destination:
        result['valid'] = False
        result['errors'].append("Destination address cannot be empty")
    elif len(destination) != 56 or not destination.startswith('G'):
        result['valid'] = False
        result['errors'].append("Invalid Stellar address format. Must start with 'G' and be 56 characters")
    elif not re.match(r'^G[A-Z2-7]{55}$', destination):
        result['valid'] = False
        result['errors'].append("Invalid characters in Stellar address. Only A-Z and 2-7 are allowed")
    
    # Validate amount
    if amount <= 0:
        result['valid'] = False
        result['errors'].append("Amount must be positive")
    elif amount < 0.0000001:
        result['valid'] = False
        result['errors'].append("Amount too small. Minimum is 0.0000001 XLM")
    elif amount > 1000000:  # Reasonable upper limit
        result['warnings'].append("Large amount detected. Please double-check the amount")
    
    # Validate against source balance if provided
    if source_balance is not None:
        total_cost = amount + 0.00001 + 1.0  # Payment + fee + minimum reserve
        if source_balance < total_cost:
            result['valid'] = False
            result['errors'].append(
                f"Insufficient balance. Required: {total_cost} XLM, Available: {source_balance} XLM"
            )
        elif source_balance < amount + 0.00001 + 2.0:
            result['warnings'].append(
                "Low balance warning. This transaction may leave your account below the recommended minimum balance"
            )
    
    return result

def format_transaction_summary(transaction_data: Dict[str, Any]) -> str:
    """
    Format transaction data for user display.
    
    Args:
        transaction_data: Transaction data from Stellar
        
    Returns:
        Formatted transaction summary
    """
    if not transaction_data:
        return "No transaction data available"
    
    summary_lines = []
    
    # Basic transaction info
    hash_val = transaction_data.get('hash', 'N/A')
    summary_lines.append(f"Transaction Hash: {hash_val}")
    
    # Status
    successful = transaction_data.get('successful', False)
    status_icon = "Success" if successful else "Failed"
    summary_lines.append(f"Status: {status_icon}")
    
    # Ledger
    ledger = transaction_data.get('ledger', 'N/A')
    if ledger != 'N/A':
        summary_lines.append(f"Ledger: {ledger}")
    
    # Timestamp
    created_at = transaction_data.get('created_at', 'N/A')
    if created_at != 'N/A':
        summary_lines.append(f"Created: {created_at}")
    
    # Fee
    fee_paid = transaction_data.get('fee_paid', 'N/A')
    if fee_paid != 'N/A':
        fee_xlm = int(fee_paid) / 10000000  # Convert stroops to XLM
        summary_lines.append(f"Fee: {fee_xlm:.7f} XLM")
    
    # Operations count
    operations = transaction_data.get('operations', [])
    if operations:
        summary_lines.append(f"Operations: {len(operations)}")
        
        # Brief description of operations
        for i, op in enumerate(operations[:3], 1):  # Show max 3 operations
            op_type = op.get('type', 'unknown')
            if op_type == 'payment':
                asset_code = op.get('asset_code', 'XLM')
                amount = op.get('amount', 'N/A')
                summary_lines.append(f"  {i}. Payment: {amount} {asset_code}")
            elif op_type == 'create_account':
                starting_balance = op.get('starting_balance', 'N/A')
                summary_lines.append(f"  {i}. Create Account: {starting_balance} XLM")
            else:
                summary_lines.append(f"  {i}. {op_type.title()}")
        
        if len(operations) > 3:
            summary_lines.append(f"  ... and {len(operations) - 3} more operations")
    
    return "\n".join(summary_lines)
