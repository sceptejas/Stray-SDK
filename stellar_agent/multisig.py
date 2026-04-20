from stellar_sdk import Server, Keypair, TransactionBuilder, TransactionEnvelope
from stellar_sdk.network import Network
from typing import List, Dict, Any, Optional

class MultisigManager:
    """Manages multi-signature transaction workflows."""
    
    def __init__(self, horizon_url: str, network_passphrase: str):
        self.server = Server(horizon_url)
        self.network_passphrase = network_passphrase

    def add_signature(self, tx_xdr: str, secret_key: str) -> str:
        """
        Adds a signature to a transaction XDR.
        
        Args:
            tx_xdr: Transaction XDR string
            secret_key: Secret key to sign with
            
        Returns:
            Updated transaction XDR string
        """
        envelope = TransactionEnvelope.from_xdr(tx_xdr, self.network_passphrase)
        keypair = Keypair.from_secret(secret_key)
        envelope.sign(keypair)
        return envelope.to_xdr()

    def merge_signatures(self, xdr_a: str, xdr_b: str) -> str:
        """
        Merges signatures from two transaction XDRs.
        
        Args:
            xdr_a: First transaction XDR
            xdr_b: Second transaction XDR
            
        Returns:
            Merged transaction XDR
        """
        envelope_a = TransactionEnvelope.from_xdr(xdr_a, self.network_passphrase)
        envelope_b = TransactionEnvelope.from_xdr(xdr_b, self.network_passphrase)
        
        # Combine signatures (set handles duplicates if hint+sig match)
        combined_signatures = list(envelope_a.signatures)
        existing_hints_sigs = set((sig.hint, sig.signature) for sig in combined_signatures)
        
        for sig in envelope_b.signatures:
            if (sig.hint, sig.signature) not in existing_hints_sigs:
                combined_signatures.append(sig)
                existing_hints_sigs.add((sig.hint, sig.signature))
        
        envelope_a.signatures = combined_signatures
        return envelope_a.to_xdr()

    def get_status(self, tx_xdr: str) -> Dict[str, Any]:
        """
        Gets the signing status of a transaction.
        
        Args:
            tx_xdr: Transaction XDR string
            
        Returns:
            Dict containing signing status, current weight, and thresholds
        """
        envelope = TransactionEnvelope.from_xdr(tx_xdr, self.network_passphrase)
        # Type check: envelope.transaction is often what we want
        transaction = envelope.transaction
        source_account_id = transaction.source.public_key
        
        # Load account to get signers and thresholds
        account_info = self.server.accounts().account_id(source_account_id).call()
        thresholds = account_info['thresholds']
        account_signers = account_info['signers']
        
        required_threshold = thresholds['med_threshold']
        
        tx_hash = envelope.hash()
        current_weight = 0
        signers_found = []
        
        for signer in account_signers:
            # Only process Ed25519 signers
            if not signer['key'].startswith('G'):
                continue
                
            keypair = Keypair.from_public_key(signer['key'])
            hint = keypair.signature_hint()
            
            has_signed = False
            for sig in envelope.signatures:
                if sig.hint == hint:
                    try:
                        keypair.verify(tx_hash, sig.signature)
                        has_signed = True
                        break
                    except:
                        continue
            
            if has_signed:
                current_weight += signer['weight']
                signers_found.append({
                    'public_key': signer['key'],
                    'weight': signer['weight']
                })
        
        return {
            'is_fully_signed': current_weight >= required_threshold,
            'current_weight': current_weight,
            'required_threshold': required_threshold,
            'missing_weight': max(0, required_threshold - current_weight),
            'signers': signers_found
        }

    def submit(self, tx_xdr: str) -> Dict[str, Any]:
        """Submits a transaction XDR to the network."""
        envelope = TransactionEnvelope.from_xdr(tx_xdr, self.network_passphrase)
        return self.server.submit_transaction(envelope)
