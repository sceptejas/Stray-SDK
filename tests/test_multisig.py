"""Unit tests for multi-signature functionality."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from stellar_agent.multisig import (
    MultiSigManager, Signer, MultiSigAccount, PendingTransaction
)
from stellar_sdk import Keypair, TransactionBuilder, Asset, Transaction
from stellar_sdk.operation import Payment, SetOptions
from stellar_sdk.exceptions import NotFoundError, BadRequestError
from decimal import Decimal


@pytest.fixture
def mock_config():
    with patch('stellar_agent.multisig.config') as mock_conf:
        mock_conf.horizon_url = 'https://horizon-testnet.stellar.org'
        mock_conf.network_passphrase = 'Test SDF Network ; September 2015'
        yield mock_conf


@pytest.fixture
def multisig_manager(mock_config):
    with patch('stellar_agent.multisig.Server') as mock_server_class:
        mock_server = mock_server_class.return_value
        manager = MultiSigManager()
        manager.server = mock_server
        yield manager


@pytest.fixture
def sample_signers():
    return [
        Signer(public_key="GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", weight=1),
        Signer(public_key="GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2", weight=1),
        Signer(public_key="GA5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2", weight=2)
    ]


class TestSigner:
    """Test Signer class."""
    
    def test_valid_signer(self):
        signer = Signer(
            public_key="GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            weight=1
        )
        assert signer.validate() is True
    
    def test_invalid_public_key(self):
        signer = Signer(public_key="INVALID", weight=1)
        assert signer.validate() is False
    
    def test_invalid_weight_too_low(self):
        signer = Signer(
            public_key="GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            weight=0
        )
        assert signer.validate() is False
    
    def test_invalid_weight_too_high(self):
        signer = Signer(
            public_key="GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            weight=256
        )
        assert signer.validate() is False


class TestMultiSigAccount:
    """Test MultiSigAccount class."""
    
    def test_valid_multisig_account(self, sample_signers):
        account = MultiSigAccount(
            account_id="GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            threshold=2,
            signers=sample_signers
        )
        is_valid, error = account.validate()
        assert is_valid is True
        assert error == ""
    
    def test_invalid_account_id(self, sample_signers):
        account = MultiSigAccount(
            account_id="INVALID",
            threshold=2,
            signers=sample_signers
        )
        is_valid, error = account.validate()
        assert is_valid is False
        assert "Invalid account ID" in error
    
    def test_invalid_threshold(self, sample_signers):
        account = MultiSigAccount(
            account_id="GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            threshold=0,
            signers=sample_signers
        )
        is_valid, error = account.validate()
        assert is_valid is False
        assert "Threshold must be between 1 and 255" in error
    
    def test_no_signers(self):
        account = MultiSigAccount(
            account_id="GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            threshold=1,
            signers=[]
        )
        is_valid, error = account.validate()
        assert is_valid is False
        assert "At least one signer is required" in error
    
    def test_insufficient_total_weight(self):
        signers = [
            Signer(public_key="GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H", weight=1)
        ]
        account = MultiSigAccount(
            account_id="GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
            threshold=2,
            signers=signers
        )
        is_valid, error = account.validate()
        assert is_valid is False
        assert "Total signer weight" in error and "is less than threshold" in error


class TestPendingTransaction:
    """Test PendingTransaction class."""
    
    def test_to_dict(self):
        pending_tx = PendingTransaction(
            transaction_xdr="AAAA",
            network_passphrase="Test Network",
            required_signatures=["G1", "G2"],
            collected_signatures={"G1": "S1"},
            created_at=1234567890,
            description="Test transaction"
        )
        
        result = pending_tx.to_dict()
        assert result['transaction_xdr'] == "AAAA"
        assert result['network_passphrase'] == "Test Network"
        assert result['required_signatures'] == ["G1", "G2"]
        assert result['collected_signatures'] == {"G1": "S1"}
        assert result['created_at'] == 1234567890
        assert result['description'] == "Test transaction"
    
    def test_from_dict(self):
        data = {
            'transaction_xdr': 'AAAA',
            'network_passphrase': 'Test Network',
            'required_signatures': ['G1', 'G2'],
            'collected_signatures': {'G1': 'S1'},
            'created_at': 1234567890,
            'description': 'Test transaction'
        }
        
        pending_tx = PendingTransaction.from_dict(data)
        assert pending_tx.transaction_xdr == "AAAA"
        assert pending_tx.network_passphrase == "Test Network"
        assert pending_tx.required_signatures == ["G1", "G2"]
        assert pending_tx.collected_signatures == {"G1": "S1"}
        assert pending_tx.created_at == 1234567890
        assert pending_tx.description == "Test transaction"


class TestMultiSigManager:
    """Test MultiSigManager class."""
    
    def test_init(self, mock_config):
        with patch('stellar_agent.multisig.Server') as mock_server_class:
            manager = MultiSigManager()
            mock_server_class.assert_called_once_with('https://horizon-testnet.stellar.org')
    
    def test_create_multisig_account_success(self, multisig_manager, sample_signers):
        # Mock server responses
        mock_master_account = Mock()
        mock_new_account = Mock()
        
        multisig_manager.server.load_account.side_effect = [mock_master_account, mock_new_account]
        
        # Mock transaction submission
        mock_fund_response = {'hash': 'fund_hash'}
        mock_multisig_response = {'hash': 'multisig_hash'}
        multisig_manager.server.submit_transaction.side_effect = [
            mock_fund_response,
            mock_multisig_response
        ]
        
        with patch('stellar_agent.multisig.Keypair') as mock_keypair_class:
            mock_master_keypair = Mock()
            mock_new_keypair = Mock()
            mock_master_keypair.public_key = "MASTER_PUBLIC"
            mock_new_keypair.public_key = "NEW_PUBLIC"
            mock_new_keypair.secret = "NEW_SECRET"
            
            mock_keypair_class.from_secret.return_value = mock_master_keypair
            mock_keypair_class.random.return_value = mock_new_keypair
            
            with patch('stellar_agent.multisig.TransactionBuilder') as mock_builder_class:
                mock_builder = Mock()
                mock_builder_class.return_value = mock_builder
                mock_tx = Mock()
                mock_builder.append_operation.return_value = mock_builder
                mock_builder.set_timeout.return_value = mock_builder
                mock_builder.build.return_value = mock_tx
                
                result = multisig_manager.create_multisig_account(
                    master_secret="MASTER_SECRET",
                    signers=sample_signers,
                    threshold=2,
                    starting_balance=1.0
                )
                
                assert result['account_id'] == "NEW_PUBLIC"
                assert result['secret'] == "NEW_SECRET"
                assert result['threshold'] == 2
                assert len(result['signers']) == 3
    
    def test_create_multisig_account_failure(self, multisig_manager, sample_signers):
        multisig_manager.server.load_account.side_effect = NotFoundError("Account not found")
        
        with pytest.raises(RuntimeError, match="Failed to create multi-signature account"):
            multisig_manager.create_multisig_account(
                master_secret="MASTER_SECRET",
                signers=sample_signers,
                threshold=2,
                starting_balance=1.0
            )
    
    def test_build_multisig_transaction_success(self, multisig_manager):
        # Mock account info
        mock_account_info = {
            'signers': [
                {'key': 'G1', 'weight': 1},
                {'key': 'G2', 'weight': 1}
            ],
            'thresholds': {
                'med_threshold': 2
            }
        }
        
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.return_value = mock_account_info
        multisig_manager.server.accounts.return_value = mock_accounts
        
        # Mock load_account
        mock_account = Mock()
        multisig_manager.server.load_account.return_value = mock_account
        
        with patch('stellar_agent.multisig.TransactionBuilder') as mock_builder_class:
            mock_builder = Mock()
            mock_builder_class.return_value = mock_builder
            mock_tx = Mock()
            mock_tx.to_xdr.return_value = "TRANSACTION_XDR"
            mock_builder.append_operation.return_value = mock_builder
            mock_builder.set_timeout.return_value = mock_builder
            mock_builder.build.return_value = mock_tx
            
            pending_tx = multisig_manager.build_multisig_transaction(
                source_account_id="SOURCE_ACCOUNT",
                destination="DESTINATION",
                amount=10.0
            )
            
            assert pending_tx.transaction_xdr == "TRANSACTION_XDR"
            assert pending_tx.required_signatures == ['G1', 'G2']
            assert "Send 10.0 XLM to DESTINATION" in pending_tx.description
    
    def test_build_multisig_transaction_failure(self, multisig_manager):
        multisig_manager.server.accounts.side_effect = NotFoundError("Account not found")
        
        with pytest.raises(RuntimeError, match="Failed to build multi-signature transaction"):
            multisig_manager.build_multisig_transaction(
                source_account_id="SOURCE_ACCOUNT",
                destination="DESTINATION",
                amount=10.0
            )
    
    def test_add_signature_success(self, multisig_manager):
        pending_tx = PendingTransaction(
            transaction_xdr="TRANSACTION_XDR",
            network_passphrase="Test Network",
            required_signatures=["G1", "G2"],
            collected_signatures={},
            created_at=1234567890,
            description="Test"
        )
        
        with patch('stellar_agent.multisig.Keypair') as mock_keypair_class:
            mock_keypair = Mock()
            mock_keypair.public_key = "G1"
            mock_keypair_class.from_secret.return_value = mock_keypair
            
            with patch('stellar_agent.multisig.Transaction') as mock_tx_class:
                mock_tx = Mock()
                mock_tx.to_xdr.return_value="SIGNED_XDR"
                mock_tx_class.from_xdr.return_value = mock_tx
                
                updated_tx = multisig_manager.add_signature(pending_tx, "SIGNER_SECRET")
                
                assert updated_tx.transaction_xdr == "SIGNED_XDR"
                assert "G1" in updated_tx.collected_signatures
                assert updated_tx.collected_signatures["G1"] == "SIGNER_SECRET"
    
    def test_add_signature_unauthorized_signer(self, multisig_manager):
        pending_tx = PendingTransaction(
            transaction_xdr="TRANSACTION_XDR",
            network_passphrase="Test Network",
            required_signatures=["G1", "G2"],
            collected_signatures={},
            created_at=1234567890,
            description="Test"
        )
        
        with patch('stellar_agent.multisig.Keypair') as mock_keypair_class:
            mock_keypair = Mock()
            mock_keypair.public_key = "G3"  # Not in required_signatures
            mock_keypair_class.from_secret.return_value = mock_keypair
            
            with pytest.raises(ValueError, match="Signer G3 is not authorized"):
                multisig_manager.add_signature(pending_tx, "SIGNER_SECRET")
    
    def test_add_signature_already_signed(self, multisig_manager):
        pending_tx = PendingTransaction(
            transaction_xdr="TRANSACTION_XDR",
            network_passphrase="Test Network",
            required_signatures=["G1", "G2"],
            collected_signatures={"G1": "S1"},
            created_at=1234567890,
            description="Test"
        )
        
        with patch('stellar_agent.multisig.Keypair') as mock_keypair_class:
            mock_keypair = Mock()
            mock_keypair.public_key = "G1"
            mock_keypair_class.from_secret.return_value = mock_keypair
            
            with pytest.raises(ValueError, match="Signer G1 has already signed"):
                multisig_manager.add_signature(pending_tx, "SIGNER_SECRET")
    
    def test_submit_multisig_transaction_success(self, multisig_manager):
        pending_tx = PendingTransaction(
            transaction_xdr="TRANSACTION_XDR",
            network_passphrase="Test Network",
            required_signatures=["G1", "G2"],
            collected_signatures={"G1": "S1", "G2": "S2"},
            created_at=1234567890,
            description="Test"
        )
        
        # Mock account info for threshold check
        mock_account_info = {
            'thresholds': {'med_threshold': 2}
        }
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.return_value = mock_account_info
        multisig_manager.server.accounts.return_value = mock_accounts
        
        # Mock transaction loading
        with patch('stellar_agent.multisig.Transaction') as mock_tx_class:
            mock_tx = Mock()
            mock_tx.source.account_id = "SOURCE_ACCOUNT"
            mock_tx_class.from_xdr.return_value = mock_tx
            
            # Mock submission
            mock_response = {'hash': 'SUBMITTED_HASH'}
            multisig_manager.server.submit_transaction.return_value = mock_response
            
            result = multisig_manager.submit_multisig_transaction(pending_tx)
            
            assert result['hash'] == 'SUBMITTED_HASH'
    
    def test_submit_multisig_transaction_insufficient_signatures(self, multisig_manager):
        pending_tx = PendingTransaction(
            transaction_xdr="TRANSACTION_XDR",
            network_passphrase="Test Network",
            required_signatures=["G1", "G2"],
            collected_signatures={"G1": "S1"},  # Only 1 signature, need 2
            created_at=1234567890,
            description="Test"
        )
        
        # Mock account info
        mock_account_info = {
            'thresholds': {'med_threshold': 2}
        }
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.return_value = mock_account_info
        multisig_manager.server.accounts.return_value = mock_accounts
        
        with pytest.raises(RuntimeError, match="Insufficient signatures"):
            multisig_manager.submit_multisig_transaction(pending_tx)
    
    def test_get_account_signers_success(self, multisig_manager):
        mock_account_info = {
            'signers': [
                {'key': 'G1', 'weight': 1},
                {'key': 'G2', 'weight': 2},
                {'key': 'G3', 'weight': 0}  # Should be filtered out
            ],
            'thresholds': {
                'low_threshold': 1,
                'med_threshold': 2,
                'high_threshold': 3
            }
        }
        
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.return_value = mock_account_info
        multisig_manager.server.accounts.return_value = mock_accounts
        
        result = multisig_manager.get_account_signers("ACCOUNT_ID")
        
        assert len(result['signers']) == 2  # G3 filtered out
        assert result['signers'][0]['public_key'] == 'G1'
        assert result['signers'][0]['weight'] == 1
        assert result['signers'][1]['public_key'] == 'G2'
        assert result['signers'][1]['weight'] == 2
        assert result['thresholds']['med_threshold'] == 2
    
    def test_get_account_signers_failure(self, multisig_manager):
        multisig_manager.server.accounts.side_effect = NotFoundError("Account not found")
        
        with pytest.raises(RuntimeError, match="Failed to get account signers"):
            multisig_manager.get_account_signers("ACCOUNT_ID")
    
    def test_validate_multisig_setup_valid(self, multisig_manager):
        mock_account_info = {
            'signers': [
                {'key': 'G1', 'weight': 1},
                {'key': 'G2', 'weight': 1}
            ],
            'thresholds': {
                'med_threshold': 2
            }
        }
        
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.return_value = mock_account_info
        multisig_manager.server.accounts.return_value = mock_accounts
        
        is_valid, message = multisig_manager.validate_multisig_setup("ACCOUNT_ID")
        
        assert is_valid is True
        assert message == "Multi-signature setup is valid"
    
    def test_validate_multisig_setup_insufficient_signers(self, multisig_manager):
        mock_account_info = {
            'signers': [
                {'key': 'G1', 'weight': 1}
            ],
            'thresholds': {
                'med_threshold': 1
            }
        }
        
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.return_value = mock_account_info
        multisig_manager.server.accounts.return_value = mock_accounts
        
        is_valid, message = multisig_manager.validate_multisig_setup("ACCOUNT_ID")
        
        assert is_valid is False
        assert "at least 2 signers" in message
    
    def test_validate_multisig_setup_insufficient_weight(self, multisig_manager):
        mock_account_info = {
            'signers': [
                {'key': 'G1', 'weight': 1},
                {'key': 'G2', 'weight': 1}
            ],
            'thresholds': {
                'med_threshold': 3  # Higher than total weight
            }
        }
        
        mock_accounts = Mock()
        mock_account_id = Mock()
        mock_accounts.account_id.return_value = mock_account_id
        mock_account_id.call.return_value = mock_account_info
        multisig_manager.server.accounts.return_value = mock_accounts
        
        is_valid, message = multisig_manager.validate_multisig_setup("ACCOUNT_ID")
        
        assert is_valid is False
        assert "Total weight" in message and "is less than threshold" in message
    
    def test_validate_multisig_setup_account_not_found(self, multisig_manager):
        multisig_manager.server.accounts.side_effect = NotFoundError("Account not found")
        
        is_valid, message = multisig_manager.validate_multisig_setup("ACCOUNT_ID")
        
        assert is_valid is False
        assert "Failed to validate multi-signature setup" in message
