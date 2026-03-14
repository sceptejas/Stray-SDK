"""Unit tests for transaction history functionality."""
import pytest
from unittest.mock import Mock, patch
from stellar_agent.client import StellarClient
from stellar_agent.history import display_transaction_history, display_transaction_summary

class TestTransactionHistory:
    """Test transaction history functionality."""
    
    @patch('stellar_agent.client.Server')
    def test_get_transaction_history_success(self, mock_server_class):
        """Test successful transaction history retrieval."""
        # Setup mock server
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        
        # Mock transaction response
        mock_transactions = {
            '_embedded': {
                'records': [
                    {
                        'hash': 'abc123def456',
                        'created_at': '2024-01-15T10:30:00Z',
                        'source_account': 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
                        'fee_charged': '100',
                        'operation_count': 1,
                        'successful': True,
                        'ledger': 12345,
                    }
                ]
            }
        }
        
        # Mock operations response
        mock_operations = {
            '_embedded': {
                'records': [
                    {
                        'type': 'payment',
                        'from': 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
                        'to': 'GDQP2KPQGKIHYJGXNUIYOMHARUARCA7DJT5FO2FFOOKY3B2WSQHG4W37',
                        'amount': '10.5',
                        'asset_type': 'native',
                    }
                ]
            }
        }
        
        # Setup mock chain
        mock_tx_builder = Mock()
        mock_tx_builder.for_account.return_value = mock_tx_builder
        mock_tx_builder.limit.return_value = mock_tx_builder
        mock_tx_builder.order.return_value = mock_tx_builder
        mock_tx_builder.call.return_value = mock_transactions
        
        mock_op_builder = Mock()
        mock_op_builder.for_transaction.return_value = mock_op_builder
        mock_op_builder.call.return_value = mock_operations
        
        mock_server.transactions.return_value = mock_tx_builder
        mock_server.operations.return_value = mock_op_builder
        
        # Create client and fetch history
        client = StellarClient()
        history = client.get_transaction_history(
            'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
            limit=10
        )
        
        # Assertions
        assert len(history) == 1
        assert history[0]['hash'] == 'abc123def456'
        assert history[0]['successful'] == True
        assert history[0]['fee_charged'] == 0.00001  # 100 stroops = 0.00001 XLM
        assert len(history[0]['operations']) == 1
        assert history[0]['operations'][0]['type'] == 'payment'
        assert history[0]['operations'][0]['amount'] == '10.5'
    
    @patch('stellar_agent.client.Server')
    def test_get_transaction_history_empty(self, mock_server_class):
        """Test transaction history with no transactions."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        
        # Mock empty response
        mock_transactions = {'_embedded': {'records': []}}
        
        mock_tx_builder = Mock()
        mock_tx_builder.for_account.return_value = mock_tx_builder
        mock_tx_builder.limit.return_value = mock_tx_builder
        mock_tx_builder.order.return_value = mock_tx_builder
        mock_tx_builder.call.return_value = mock_transactions
        
        mock_server.transactions.return_value = mock_tx_builder
        
        client = StellarClient()
        history = client.get_transaction_history(
            'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
            limit=10
        )
        
        assert len(history) == 0
    
    @patch('stellar_agent.client.Server')
    def test_get_transaction_history_filters_failed(self, mock_server_class):
        """Test that failed transactions are filtered by default."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        
        # Mock response with successful and failed transactions
        mock_transactions = {
            '_embedded': {
                'records': [
                    {
                        'hash': 'success123',
                        'created_at': '2024-01-15T10:30:00Z',
                        'source_account': 'GTEST',
                        'fee_charged': '100',
                        'operation_count': 1,
                        'successful': True,
                        'ledger': 12345,
                    },
                    {
                        'hash': 'failed456',
                        'created_at': '2024-01-15T10:29:00Z',
                        'source_account': 'GTEST',
                        'fee_charged': '100',
                        'operation_count': 1,
                        'successful': False,
                        'ledger': 12344,
                    }
                ]
            }
        }
        
        mock_tx_builder = Mock()
        mock_tx_builder.for_account.return_value = mock_tx_builder
        mock_tx_builder.limit.return_value = mock_tx_builder
        mock_tx_builder.order.return_value = mock_tx_builder
        mock_tx_builder.call.return_value = mock_transactions
        
        mock_server.transactions.return_value = mock_tx_builder
        mock_server.operations.return_value = Mock()
        
        client = StellarClient()
        
        # Test with include_failed=False (default)
        history = client.get_transaction_history('GTEST', limit=10, include_failed=False)
        assert len(history) == 1
        assert history[0]['hash'] == 'success123'
        
        # Test with include_failed=True
        history_all = client.get_transaction_history('GTEST', limit=10, include_failed=True)
        assert len(history_all) == 2
    
    def test_display_transaction_history_empty(self, capsys):
        """Test displaying empty transaction history."""
        display_transaction_history([], 'GTEST')
        captured = capsys.readouterr()
        assert "No transactions found" in captured.out
    
    def test_display_transaction_summary(self, capsys):
        """Test transaction summary display."""
        transactions = [
            {
                'hash': 'test123',
                'created_at': '2024-01-15T10:30:00Z',
                'source_account': 'GTEST',
                'fee_charged': 0.00001,
                'successful': True,
                'ledger': 12345,
                'operations': [
                    {
                        'type': 'payment',
                        'from': 'GTEST',
                        'to': 'GOTHER',
                        'amount': '10.5',
                    }
                ]
            }
        ]
        
        display_transaction_summary(transactions, 'GTEST')
        captured = capsys.readouterr()
        
        assert "Transaction Summary" in captured.out
        assert "Total Sent: 10.5" in captured.out
        assert "Total Fees Paid: 0.0000100" in captured.out
