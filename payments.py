
from stellar_sdk import Server, Keypair, TransactionBuilder, Network
from config import HORIZON_URL, NETWORK_PASSPHRASE

server = Server(HORIZON_URL)

def send_payment(source_secret, destination_public, amount):
    source_keypair = Keypair.from_secret(source_secret)
    source_account = server.load_account(source_keypair.public_key)

    transaction = (
        TransactionBuilder(
            source_account=source_account,
            network_passphrase=NETWORK_PASSPHRASE,
            base_fee=100,
        )
        .append_payment_op(destination=destination_public, amount=str(amount), asset_code="XLM")
        .set_timeout(30)
        .build()
    )

    transaction.sign(source_keypair)
    response = server.submit_transaction(transaction)
    return response