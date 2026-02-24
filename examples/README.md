# Stray SDK Examples

Practical examples demonstrating how to use Stray SDK.

## Setup

1. Install Stray SDK:
```bash
cd ..
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp ../.env.example .env
# Edit .env with your credentials
```

## Examples

### 1. Send Payment
Basic example of sending XLM payment.
```bash
python send_payment.py
```

### 2. Check Balance
Check account balance and info.
```bash
python check_balance.py
```

### 3. Batch Payments
Send multiple payments in sequence.
```bash
python batch_payments.py
```

## Configuration

All examples require `.env` configuration:
```env
SOURCE_SECRET=YOUR_SECRET_KEY
MONITOR_ACCOUNT_ID=YOUR_PUBLIC_KEY
HORIZON_URL=https://horizon-testnet.stellar.org
NETWORK_PASSPHRASE=Test SDF Network ; September 2015
```

## Running on Testnet

All examples use testnet by default. To use mainnet:
1. Update `HORIZON_URL` to `https://horizon.stellar.org`
2. Update `NETWORK_PASSPHRASE` to `Public Global Stellar Network ; September 2015`
3. ⚠️ Use real funds with caution!

## Additional Resources

- [Stellar SDK Documentation](https://stellar-sdk.readthedocs.io/)
- [Stray SDK GitHub](https://github.com/sceptejas/Stray-SDK)
