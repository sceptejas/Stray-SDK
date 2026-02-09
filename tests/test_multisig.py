"""Tests for multisig functionality."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from stellar_agent.client import StellarClient, MultisigInfo
from stellar_sdk import TransactionEnvelope, Keypair


class TestMultisigInfo:
    """Test MultisigInfo class."""
    
    def test_single_sig_account(self):
        """Test single signature account."""
        info = MultisigInfo(required_threshold=1, current_weight=1, signers=[])
        assert info.is_multisig_required is False
        assert info.needs_additional_signatures is False
    
    def test_multisig_account(self):
        """Test multi signature account."""
        info = MultisigInfo(required_threshold=2, current_weight=3, signers=[])
        assert info.is_multisig_required is True
        assert info.needs_additional_signatures is False
    
    def test_multisig_needs_more_signatures(self):
        """Test multisig account needing more signatures."""
        info = MultisigInfo(required_threshold=3, current_weight=2, signers=[])
        assert info.is_multisig_required is True
        assert info.needs_additional_signatures is True


class TestStellarClientMultisig:
    """Test StellarClient multisig functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a StellarClient instance for testing."""
        return StellarClient()
    
    @pytest.fixture
    def mock_server(self):
        """Create a mock server."""
        return Mock()
    
    @pytest.fixture
    def sample_account_info(self):
        """Sample account info for testing."""
        return {
            'account_id': 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
            'thresholds': {
                'low_threshold': 1,
                'med_threshold': 2,
                'high_threshold': 3
            },
            'signers': [
                {
                    'key': 'GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
                    'weight': 1,
                    'type': 'ed25519_public_key'
                },
                {
                    'key': 'GC2BKLYOOYPDEFJKLKY6FNNRQMGFLVHJKQRGNSSRRGSMPGF32LHCQVGF',
                    'weight': 1,
                    'type': 'ed25519_public_key'
                }
            ]
        }
    
    @patch('stellar_agent.client.StellarClient.get_account_info')
    def test_get_multisig_info_single_sig(self, mock_get_account, client):
        """Test getting multisig info for single sig account."""
        mock_get_account.return_value = {
            'thresholds': {'low_threshold': 1, 'med_threshold': 1},
            'signers': [{'key': 'GTEST', 'weight': 1}]
        }
        
        info = client.get_multisig_info('GTEST')
        
        assert info.required_threshold == 1
        assert info.current_weight == 1
        assert info.is_multisig_required is False
    
    @patch('stellar_agent.client.StellarClient.get_account_info')
    def test_get_multisig_info_multisig(self, mock_get_account, client, sample_account_info):
        """Test getting multisig info for multisig account."""
        mock_get_account.return_value = sample_account_info
        
        info = client.get_multisig_info('GTEST')
        
        assert info.required_threshold == 2  # max of low=1, med=2
        assert info.current_weight == 2  # sum of signer weights
        assert info.is_multisig_required is True
        assert len(info.signers) == 2
    
    @patch('stellar_agent.client.StellarClient.get_multisig_info')
    def test_check_if_multisig_required(self, mock_get_multisig, client):
        """Test checking if multisig is required."""
        # Mock the multisig info
        mock_multisig_info = MultisigInfo(required_threshold=2, current_weight=2, signers=[])
        mock_get_multisig.return_value = mock_multisig_info
        
        # Test secret key (test key, not real)
        test_secret = "SCZANGBA5YHTNYVVV4C3U252E2B6P6F5T3U6MM63WBSBZATAQI3EBTQ4"
        
        is_multisig, info = client.check_if_multisig_required(test_secret)
        
        assert is_multisig is True
        assert info.required_threshold == 2
    
    def test_export_import_xdr(self, client):
        """Test XDR export and import functionality."""
        # Create a mock transaction envelope
        mock_transaction = Mock(spec=TransactionEnvelope)
        mock_transaction.to_xdr.return_value = "MOCK_XDR_STRING"
        
        # Test export
        xdr = client.export_transaction_xdr(mock_transaction)
        assert xdr == "MOCK_XDR_STRING"
        
        # Test import with invalid XDR (should raise ValueError)
        with pytest.raises(ValueError):
            client.import_transaction_xdr("invalid_xdr")
    
    def test_get_transaction_signature_count(self, client):
        """Test getting signature count from transaction."""
        # Create mock transaction with signatures
        mock_transaction = Mock(spec=TransactionEnvelope)
        mock_transaction.signatures = ['sig1', 'sig2']
        
        count = client.get_transaction_signature_count(mock_transaction)
        assert count == 2
    
    @patch('stellar_agent.client.StellarClient.get_multisig_info')
    def test_get_transaction_info(self, mock_get_multisig, client):
        """Test getting transaction information."""
        # Mock multisig info
        mock_multisig_info = MultisigInfo(required_threshold=2, current_weight=2, signers=[])
        mock_get_multisig.return_value = mock_multisig_info
        
        # Create mock transaction
        mock_tx = Mock()
        mock_tx.source_account_id = 'GTEST'
        mock_tx.operations = [Mock(), Mock()]  # 2 operations
        mock_tx.sequence = 123456789
        mock_tx.fee = 1000
        
        mock_transaction = Mock(spec=TransactionEnvelope)
        mock_transaction.transaction = mock_tx
        mock_transaction.signatures = ['sig1']  # 1 signature
        
        info = client.get_transaction_info(mock_transaction)
        
        assert info['source_account'] == 'GTEST'
        assert info['signature_count'] == 1
        assert info['required_threshold'] == 2
        assert info['is_ready_to_submit'] is False
        assert info['needs_more_signatures'] is True
        assert info['operations_count'] == 2
        assert info['sequence_number'] == 123456789
        assert info['fee'] == 1000
    
    def test_can_submit_transaction_insufficient_sigs(self, client):
        """Test can_submit_transaction with insufficient signatures."""
        with patch.object(client, 'get_transaction_info') as mock_get_info:
            mock_get_info.return_value = {
                'signature_count': 1,
                'required_threshold': 2,
                'is_ready_to_submit': False
            }
            
            mock_transaction = Mock(spec=TransactionEnvelope)
            can_submit, reason = client.can_submit_transaction(mock_transaction)
            
            assert can_submit is False
            assert "Need 1 more signature(s)" in reason
    
    def test_can_submit_transaction_sufficient_sigs(self, client):
        """Test can_submit_transaction with sufficient signatures."""
        with patch.object(client, 'get_transaction_info') as mock_get_info:
            mock_get_info.return_value = {
                'signature_count': 2,
                'required_threshold': 2,
                'is_ready_to_submit': True
            }
            
            mock_transaction = Mock(spec=TransactionEnvelope)
            can_submit, reason = client.can_submit_transaction(mock_transaction)
            
            assert can_submit is True
            assert "sufficient signatures" in reason
    
    def test_submit_signed_transaction_insufficient_sigs(self, client):
        """Test submitting transaction with insufficient signatures."""
        with patch.object(client, 'can_submit_transaction') as mock_can_submit:
            mock_can_submit.return_value = (False, "Not enough signatures")
            
            mock_transaction = Mock(spec=TransactionEnvelope)
            
            with pytest.raises(ValueError, match="Cannot submit transaction"):
                client.submit_signed_transaction(mock_transaction)
    
    @patch('stellar_agent.client.StellarClient.can_submit_transaction')
    @patch('stellar_agent.client.Server')
    def test_submit_signed_transaction_success(self, mock_server_class, mock_can_submit, client):
        """Test successful transaction submission."""
        # Mock the server instance
        mock_server = Mock()
        mock_server.submit_transaction.return_value = {'hash': 'test_hash'}
        mock_server_class.return_value = mock_server
        
        # Create a new client instance to get the mocked server
        test_client = StellarClient()
        
        mock_can_submit.return_value = (True, "Sufficient signatures")
        
        mock_transaction = Mock(spec=TransactionEnvelope)
        
        response = test_client.submit_signed_transaction(mock_transaction)
        
        assert response['hash'] == 'test_hash'
        mock_server.submit_transaction.assert_called_once_with(mock_transaction)


if __name__ == '__main__':
    pytest.main([__file__])