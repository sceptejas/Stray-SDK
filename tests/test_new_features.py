"""Tests for new Stellar Agent features."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from stellar_agent.client import StellarClient
from stellar_agent.config import config

@pytest.fixture
def mock_config():
    with patch('stellar_agent.client.config') as mock_conf:
        mock_conf.horizon_url = 'https://horizon-testnet.stellar.org'
        mock_conf.network_passphrase = 'Test SDF Network ; September 2015'
        yield mock_conf

class TestTransactionHistory:
    """Test transaction history functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = StellarClient()
        self.test_account_id = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
    
    @patch('stellar_agent.client.Server')
    def test_get_transaction_history_success(self, mock_server_class):
        """Test successful transaction history retrieval."""
        mock_server = mock_server_class.return_value
        
        # Mock the transactions call chain
        mock_transactions = Mock()
        mock_server.transactions.return_value = mock_transactions
        mock_for_account = Mock()
        mock_transactions.for_account.return_value = mock_for_account
        mock_limit = Mock()
        mock_for_account.limit.return_value = mock_limit
        mock_limit.call.return_value = {
            '_embedded': {
                'records': [
                    {
                        'hash': 'abc123',
                        'type': 'payment',
                        'created_at': '2023-01-01T00:00:00Z',
                        'successful': True,
                        'ledger': 12345
                    }
                ]
            }
        }
        
        result = self.client.get_transaction_history(self.test_account_id, 5)
        
        assert len(result) == 1
        assert result[0]['hash'] == 'abc123'
        assert result[0]['type'] == 'payment'
        mock_server.transactions.assert_called_once()
        mock_transactions.for_account.assert_called_once_with(self.test_account_id)
        mock_for_account.limit.assert_called_once_with(5)
    
    @patch('stellar_agent.client.Server')
    def test_get_transaction_history_empty(self, mock_server_class):
        """Test transaction history with no transactions."""
        mock_server = mock_server_class.return_value
        
        mock_transactions = Mock()
        mock_server.transactions.return_value = mock_transactions
        mock_for_account = Mock()
        mock_transactions.for_account.return_value = mock_for_account
        mock_limit = Mock()
        mock_for_account.limit.return_value = mock_limit
        mock_limit.call.return_value = {'_embedded': {'records': []}}
        
        result = self.client.get_transaction_history(self.test_account_id)
        
        assert result == []
    
    @patch('stellar_agent.client.Server')
    def test_get_transaction_history_account_not_found(self, mock_server_class):
        """Test transaction history for non-existent account."""
        mock_server = mock_server_class.return_value
        mock_server.transactions.side_effect = Exception("Account not found")
        
        with pytest.raises(RuntimeError, match="Failed to fetch transaction history"):
            self.client.get_transaction_history(self.test_account_id)

class TestTransactionStatus:
    """Test transaction status functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = StellarClient()
        self.test_tx_hash = "abc123def456789"
    
    @patch('stellar_agent.client.Server')
    def test_get_transaction_status_success(self, mock_server_class):
        """Test successful transaction status retrieval."""
        mock_server = mock_server_class.return_value
        
        mock_transactions = Mock()
        mock_server.transactions.return_value = mock_transactions
        mock_transaction = Mock()
        mock_transactions.transaction.return_value = mock_transaction
        mock_transaction.call.return_value = {
            'hash': self.test_tx_hash,
            'ledger': 12345,
            'successful': True,
            'created_at': '2023-01-01T00:00:00Z',
            'fee_paid': 100
        }
        
        result = self.client.get_transaction_status(self.test_tx_hash)
        
        assert result['hash'] == self.test_tx_hash
        assert result['successful'] is True
        assert result['ledger'] == 12345
        mock_transactions.transaction.assert_called_once_with(self.test_tx_hash)
    
    @patch('stellar_agent.client.Server')
    def test_get_transaction_status_not_found(self, mock_server_class):
        """Test transaction status for non-existent transaction."""
        mock_server = mock_server_class.return_value
        mock_transactions = Mock()
        mock_server.transactions.return_value = mock_transactions
        mock_transaction = Mock()
        mock_transactions.transaction.return_value = mock_transaction
        mock_transaction.call.side_effect = Exception("Transaction not found")
        
        with pytest.raises(RuntimeError, match="Failed to fetch transaction status"):
            self.client.get_transaction_status(self.test_tx_hash)

class TestAccountCreation:
    """Test account creation functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = StellarClient()
        self.test_secret = "SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
    
    @patch('stellar_agent.client.Keypair')
    @patch('stellar_agent.client.TransactionBuilder')
    @patch('stellar_agent.client.CreateAccount')
    @patch('stellar_agent.client.Server')
    def test_create_account_success(self, mock_server_class, mock_create_account_class, 
                                   mock_tx_builder_class, mock_keypair_class):
        """Test successful account creation."""
        # Mock Server
        mock_server = mock_server_class.return_value
        
        # Mock new keypair
        mock_new_keypair = Mock()
        mock_new_keypair.public_key = "GDNEW1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        mock_new_keypair.secret = "SNEW1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        mock_keypair_class.random.return_value = mock_new_keypair
        
        # Mock source keypair
        mock_source_keypair = Mock()
        mock_source_keypair.public_key = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        mock_keypair_class.from_secret.return_value = mock_source_keypair
        
        # Mock account loading
        mock_source_account = Mock()
        mock_server.load_account.return_value = mock_source_account
        
        # Mock transaction building
        mock_tx_builder = mock_tx_builder_class.return_value
        mock_tx_builder.append_operation.return_value = mock_tx_builder
        mock_tx_builder.set_timeout.return_value = mock_tx_builder
        mock_transaction = Mock()
        mock_tx_builder.build.return_value = mock_transaction
        
        # Mock transaction submission
        expected_response = {"hash": "abc123def456"}
        mock_server.submit_transaction.return_value = expected_response
        
        public_key, secret_key = self.client.create_account(self.test_secret, 2.0)
        
        assert public_key == "GDNEW1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        assert secret_key == "SNEW1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        # Verify method calls
        mock_keypair_class.random.assert_called_once()
        mock_keypair_class.from_secret.assert_called_once_with(self.test_secret)
        mock_server.load_account.assert_called_once_with("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H")
        mock_create_account_class.assert_called_once_with(
            destination="GDNEW1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            starting_balance="2.0"
        )
        mock_transaction.sign.assert_called_once_with(mock_source_keypair)
        mock_server.submit_transaction.assert_called_once_with(mock_transaction)
    
    @patch('stellar_agent.client.Keypair')
    @patch('stellar_agent.client.Server')
    def test_create_account_insufficient_balance(self, mock_server_class, mock_keypair_class):
        """Test account creation with insufficient balance."""
        mock_server = mock_server_class.return_value
        mock_server.load_account.side_effect = Exception("Insufficient balance")
        
        mock_new_keypair = Mock()
        mock_new_keypair.public_key = "GDNEW1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        mock_new_keypair.secret = "SNEW1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        mock_keypair_class.random.return_value = mock_new_keypair
        
        with pytest.raises(RuntimeError, match="Account creation failed"):
            self.client.create_account(self.test_secret, 2.0)

class TestDetailedBalance:
    """Test detailed balance functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = StellarClient()
        self.test_account_id = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
    
    @patch.object(StellarClient, 'get_account_info')
    def test_get_account_balance_detailed_success(self, mock_get_account_info):
        """Test successful detailed balance retrieval."""
        mock_get_account_info.return_value = {
            'balances': [
                {
                    'asset_type': 'native',
                    'balance': '100.5000000',
                    'buying_liabilities': '10.0000000',
                    'selling_liabilities': '5.0000000'
                },
                {
                    'asset_type': 'credit_alphanum4',
                    'asset_code': 'USD',
                    'balance': '50.0000000',
                    'limit': '1000.0000000',
                    'buying_liabilities': '0.0000000',
                    'selling_liabilities': '0.0000000'
                }
            ],
            'sequence': '123456',
            'num_subentries': 2,
            'thresholds': {'low_threshold': 1, 'med_threshold': 2, 'high_threshold': 3},
            'flags': {'auth_required': False, 'auth_revocable': False}
        }
        
        result = self.client.get_account_balance_detailed(self.test_account_id)
        
        assert result['account_id'] == self.test_account_id
        assert result['sequence'] == '123456'
        assert result['num_subentries'] == 2
        assert len(result['balances']) == 2
        
        # Check XLM balance
        xlm_balance = next(b for b in result['balances'] if b['asset_code'] == 'XLM')
        assert xlm_balance['balance'] == '100.5000000'
        assert xlm_balance['available'] == '85.5000000'  # 100.5 - 10 - 5
        
        # Check USD balance
        usd_balance = next(b for b in result['balances'] if b['asset_code'] == 'USD')
        assert usd_balance['balance'] == '50.0000000'
        assert usd_balance['limit'] == '1000.0000000'
        assert usd_balance['available'] == '50.0000000'
    
    @patch.object(StellarClient, 'get_account_info')
    def test_get_account_balance_detailed_no_balances(self, mock_get_account_info):
        """Test detailed balance with no balances."""
        mock_get_account_info.return_value = {
            'balances': [],
            'sequence': '1',
            'num_subentries': 0,
            'thresholds': {},
            'flags': {}
        }
        
        result = self.client.get_account_balance_detailed(self.test_account_id)
        
        assert result['account_id'] == self.test_account_id
        assert len(result['balances']) == 0
    
    @patch.object(StellarClient, 'get_account_info')
    def test_get_account_balance_detailed_error(self, mock_get_account_info):
        """Test detailed balance with account not found."""
        mock_get_account_info.side_effect = RuntimeError("Account not found")
        
        with pytest.raises(RuntimeError, match="Failed to get detailed balance"):
            self.client.get_account_balance_detailed(self.test_account_id)

class TestCLIIntegration:
    """Test CLI integration with new features."""
    
    @patch('stellar_agent.cli.StellarClient')
    @patch('stellar_agent.cli.config')
    def test_cli_menu_display(self, mock_config, mock_client_class):
        """Test that CLI menu displays correctly."""
        mock_config.validate.return_value = True
        mock_config.get_source_public_key.return_value = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        
        # Mock the client instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Test that we can import and access the show_main_menu function
        from stellar_agent.cli import show_main_menu
        
        # This should not raise any exceptions
        show_main_menu()
    
    @patch('stellar_agent.cli.StellarClient')
    @patch('stellar_agent.cli.config')
    @patch('builtins.input')
    def test_cli_transaction_history_flow(self, mock_input, mock_config, mock_client_class):
        """Test CLI transaction history flow."""
        mock_config.validate.return_value = True
        mock_config.get_source_public_key.return_value = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_transaction_history.return_value = [
            {'hash': 'abc123', 'type': 'payment', 'created_at': '2023-01-01T00:00:00Z', 'successful': True, 'ledger': 12345}
        ]
        
        # Simulate user input: empty account (use source), default limit, then exit
        mock_input.side_effect = ['', '', '7']
        
        from stellar_agent.cli import prompt_and_send
        
        # This should run without exceptions (though we can't easily test the full flow in unit tests)
        try:
            prompt_and_send()
        except SystemExit:
            pass  # Expected when user chooses to exit
