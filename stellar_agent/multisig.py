"""
Multi-Signature (Multisig) transaction support for the Stellar Agent.

This module implements multi-signature transaction workflows on the Stellar
blockchain, allowing transactions to be signed by multiple parties before
submission. Supports both M-of-N threshold signers and co-signer collections.

Stellar Multisig Reference:
    https://developers.stellar.org/docs/learn/encyclopedia/signatures-multisig
"""

from __future__ import annotations

import base64
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple

from stellar_sdk import (
    Server,
    Keypair,
    TransactionBuilder,
    TransactionEnvelope,
    Asset,
    Network,
)
from stellar_sdk.operation import Payment, SetOptions
from stellar_sdk.signer import Signer
from stellar_sdk.exceptions import NotFoundError, BadRequestError

from .config import config


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _keypair_from_secret(secret: str) -> Keypair:
    """Create a Keypair from a secret key, with a clear error on failure."""
    try:
        return Keypair.from_secret(secret)
    except Exception as exc:
        raise ValueError(f"Invalid secret key provided: {exc}") from exc


def _public_from_secret(secret: str) -> str:
    """Derive the public key from a secret key string."""
    return _keypair_from_secret(secret).public_key


# ---------------------------------------------------------------------------
# MultiSigClient
# ---------------------------------------------------------------------------

class MultiSigClient:
    """
    Client for building and submitting multi-signature Stellar transactions.

    Workflow
    --------
    1. The **initiator** calls :meth:`build_multisig_payment` to create a
       base-64 encoded transaction envelope (XDR).
    2. Each additional **co-signer** receives the XDR and calls
       :meth:`sign_transaction` to add their signature, returning the updated
       XDR.
    3. Once enough signatures have been collected, any party calls
       :meth:`submit_transaction` to broadcast to the network.

    This three-step design means the XDR can be passed out-of-band (e.g.
    via email, a shared file, or an API) between parties who may not be
    online simultaneously.

    Examples
    --------
    >>> client = MultiSigClient()
    >>> xdr = client.build_multisig_payment(
    ...     source_secret="SA...",
    ...     destination_public="GB...",
    ...     amount=50,
    ...     signers=["SA...", "SB..."],   # all sign immediately
    ... )
    >>> result = client.submit_transaction(xdr)
    >>> print(result["hash"])
    """

    def __init__(self) -> None:
        self.server = Server(config.horizon_url)
        self.network_passphrase = config.network_passphrase

    # ------------------------------------------------------------------
    # Core transaction building
    # ------------------------------------------------------------------

    def build_multisig_payment(
        self,
        source_secret: str,
        destination_public: str,
        amount: float,
        signers: Optional[List[str]] = None,
        memo: str = "",
        timeout: int = 30,
    ) -> str:
        """
        Build a multi-signature XLM payment transaction envelope.

        The source account must already have its multisig thresholds
        configured on-chain (see :meth:`configure_multisig_account`).
        The transaction is signed immediately by ``source_secret`` and by
        every secret key listed in ``signers``; the result is returned as a
        base-64 XDR string ready for additional signatures or submission.

        Parameters
        ----------
        source_secret:
            Secret key of the source / fee-paying account.
        destination_public:
            Public key of the payment recipient.
        amount:
            Amount of XLM to send (must be > 0).
        signers:
            Optional list of *additional* secret keys that should sign the
            transaction immediately (in addition to ``source_secret``).
        memo:
            Optional text memo to attach to the transaction (≤ 28 bytes).
        timeout:
            Transaction timeout in seconds (default 30).

        Returns
        -------
        str
            Base-64 encoded XDR of the signed transaction envelope.

        Raises
        ------
        ValueError
            If any key is invalid, the amount is non-positive, or the
            destination address is malformed.
        RuntimeError
            If the source account cannot be loaded from Horizon.
        """
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        source_keypair = _keypair_from_secret(source_secret)
        source_public = source_keypair.public_key

        try:
            source_account = self.server.load_account(source_public)
        except NotFoundError:
            raise RuntimeError(
                f"Source account {source_public} not found on the network. "
                "Ensure the account is funded."
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load source account: {exc}. "
                "Check network connectivity and Horizon URL."
            ) from exc

        builder = TransactionBuilder(
            source_account=source_account,
            network_passphrase=self.network_passphrase,
            base_fee=100,
        )

        builder.append_operation(
            Payment(
                destination=destination_public,
                asset=Asset.native(),
                amount=str(amount),
            )
        )

        if memo:
            builder.add_text_memo(memo[:28])

        builder.set_timeout(timeout)
        transaction = builder.build()

        # Sign with the source key first
        transaction.sign(source_keypair)

        # Sign with any immediately-available co-signers
        if signers:
            for secret in signers:
                kp = _keypair_from_secret(secret)
                transaction.sign(kp)

        return transaction.to_xdr()

    # ------------------------------------------------------------------
    # Incremental signing (pass-around workflow)
    # ------------------------------------------------------------------

    def sign_transaction(self, xdr: str, signer_secret: str) -> str:
        """
        Add a co-signer's signature to an existing transaction envelope.

        Parameters
        ----------
        xdr:
            Base-64 encoded XDR of the transaction envelope to sign.
        signer_secret:
            Secret key of the co-signer.

        Returns
        -------
        str
            Updated base-64 encoded XDR with the new signature appended.

        Raises
        ------
        ValueError
            If the XDR or secret key is invalid.
        """
        try:
            envelope = TransactionEnvelope.from_xdr(xdr, self.network_passphrase)
        except Exception as exc:
            raise ValueError(f"Invalid transaction XDR: {exc}") from exc

        kp = _keypair_from_secret(signer_secret)
        envelope.sign(kp)
        return envelope.to_xdr()

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------

    def submit_transaction(self, xdr: str) -> Dict[str, Any]:
        """
        Submit a fully-signed transaction envelope to the Stellar network.

        Parameters
        ----------
        xdr:
            Base-64 encoded XDR of the transaction envelope (must carry
            enough signatures to satisfy the source account's threshold).

        Returns
        -------
        dict
            Horizon response dictionary containing at minimum ``hash`` and
            ``ledger`` keys on success.

        Raises
        ------
        ValueError
            If the XDR is malformed.
        RuntimeError
            If the transaction is rejected by Horizon.
        """
        try:
            envelope = TransactionEnvelope.from_xdr(xdr, self.network_passphrase)
        except Exception as exc:
            raise ValueError(f"Invalid transaction XDR: {exc}") from exc

        try:
            response = self.server.submit_transaction(envelope)
            return response
        except BadRequestError as exc:
            detail = getattr(exc, 'message', str(exc)).lower()
            if "bad_auth" in detail or "threshold" in detail:
                raise RuntimeError(
                    "Transaction rejected: insufficient signatures. "
                    "Ensure all required co-signers have signed the transaction."
                )
            if "insufficient balance" in detail:
                raise RuntimeError(
                    "Transaction rejected: insufficient balance for payment and fees."
                )
            raise RuntimeError(f"Transaction submission failed: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(
                f"Unexpected error during submission: {exc}. "
                "Check network connectivity."
            ) from exc

    # ------------------------------------------------------------------
    # Account management
    # ------------------------------------------------------------------

    def configure_multisig_account(
        self,
        source_secret: str,
        co_signer_public_keys: List[str],
        signer_weight: int = 1,
        low_threshold: int = 2,
        med_threshold: int = 2,
        high_threshold: int = 2,
    ) -> Dict[str, Any]:
        """
        Configure a Stellar account for multi-signature operation.

        This sets the account's signing thresholds and adds one or more
        co-signers with the specified weight. The operation is submitted
        immediately using the master key of the source account.

        Parameters
        ----------
        source_secret:
            Master secret of the account to configure.
        co_signer_public_keys:
            List of public keys to add as co-signers.
        signer_weight:
            Weight to assign to each new co-signer (default 1).
        low_threshold:
            Minimum cumulative weight required for low-security operations.
        med_threshold:
            Minimum cumulative weight required for medium-security operations
            (payments fall under this category).
        high_threshold:
            Minimum cumulative weight required for high-security operations
            (changing signers, etc.).

        Returns
        -------
        dict
            Horizon response for the SetOptions transaction.

        Raises
        ------
        RuntimeError
            If account load or submission fails.

        Notes
        -----
        After calling this method, the source account requires at least
        ``med_threshold`` cumulative signature weight for payment
        transactions. The master key retains weight 1 by default, so in a
        2-of-2 setup (master + one co-signer, each weight 1, threshold 2),
        *both* must sign every payment.
        """
        source_keypair = _keypair_from_secret(source_secret)
        source_public = source_keypair.public_key

        try:
            source_account = self.server.load_account(source_public)
        except NotFoundError:
            raise RuntimeError(
                f"Account {source_public} not found. Ensure it is funded."
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load account: {exc}"
            ) from exc

        builder = TransactionBuilder(
            source_account=source_account,
            network_passphrase=self.network_passphrase,
            base_fee=100,
        )

        # Set thresholds
        builder.append_operation(
            SetOptions(
                low_threshold=low_threshold,
                med_threshold=med_threshold,
                high_threshold=high_threshold,
            )
        )

        # Add each co-signer
        for co_pub in co_signer_public_keys:
            builder.append_operation(
                SetOptions(
                    signer=Signer.ed25519_public_key(co_pub, weight=signer_weight)
                )
            )

        builder.set_timeout(30)
        transaction = builder.build()
        transaction.sign(source_keypair)

        try:
            return self.server.submit_transaction(transaction)
        except BadRequestError as exc:
            raise RuntimeError(
                f"Failed to configure multisig account: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Inspection utilities
    # ------------------------------------------------------------------

    def get_signers(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Return the list of signers and their weights for an account.

        Parameters
        ----------
        account_id:
            Public key of the account to inspect.

        Returns
        -------
        list of dict
            Each dict contains ``key``, ``weight``, and ``type`` fields as
            returned by Horizon.

        Raises
        ------
        RuntimeError
            If the account cannot be fetched.
        """
        try:
            info = self.server.accounts().account_id(account_id).call()
            return info.get("signers", [])
        except NotFoundError:
            raise RuntimeError(f"Account {account_id} not found.")
        except Exception as exc:
            raise RuntimeError(
                f"Failed to fetch account signers: {exc}"
            ) from exc

    def get_thresholds(self, account_id: str) -> Dict[str, int]:
        """
        Return the signing thresholds for an account.

        Parameters
        ----------
        account_id:
            Public key of the account to inspect.

        Returns
        -------
        dict
            Dictionary with keys ``low_threshold``, ``med_threshold``, and
            ``high_threshold``.

        Raises
        ------
        RuntimeError
            If the account cannot be fetched.
        """
        try:
            info = self.server.accounts().account_id(account_id).call()
            thresholds = info.get("thresholds", {})
            return {
                "low_threshold": thresholds.get("low_threshold", 0),
                "med_threshold": thresholds.get("med_threshold", 0),
                "high_threshold": thresholds.get("high_threshold", 0),
            }
        except NotFoundError:
            raise RuntimeError(f"Account {account_id} not found.")
        except Exception as exc:
            raise RuntimeError(
                f"Failed to fetch account thresholds: {exc}"
            ) from exc

    def count_signatures(self, xdr: str) -> int:
        """
        Return the number of signatures currently on a transaction envelope.

        Parameters
        ----------
        xdr:
            Base-64 encoded XDR of the transaction envelope.

        Returns
        -------
        int
            Number of signatures present.

        Raises
        ------
        ValueError
            If the XDR is malformed.
        """
        try:
            envelope = TransactionEnvelope.from_xdr(xdr, self.network_passphrase)
            return len(envelope.signatures)
        except Exception as exc:
            raise ValueError(f"Invalid transaction XDR: {exc}") from exc
