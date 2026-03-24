# Stray SDK

Stray SDK is a lightweight Python CLI tool for sending XLM payments on the Stellar network.

## Features

- Interactive command-line flow for sending XLM payments
- Validation for destination addresses, amounts, and environment configuration
- Testnet and mainnet network profiles via environment variables
- Optional balance safety checks before submitting a transaction

## Installation

```bash
git clone https://github.com/sceptejas/Stray-SDK.git
cd Stray-SDK
pip install -r requirements.txt
```

To install the CLI locally:

```bash
pip install -e .
stellar-agent
```

## Configuration

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

### Required variables

```env
SOURCE_SECRET=YOUR_STELLAR_SECRET_SEED
```

### Optional variables

```env
STELLAR_NETWORK=testnet
HORIZON_URL=https://horizon-testnet.stellar.org
NETWORK_PASSPHRASE=Test SDF Network ; September 2015
MONITOR_ACCOUNT_ID=G...
DESTINATION_ACCOUNT_ID=G...
MINIMUM_BALANCE_XLM=1.0
BALANCE_CHECK_ENABLED=true
```

Notes:

- `STELLAR_NETWORK` supports `testnet` and `mainnet`
- `HORIZON_URL` and `NETWORK_PASSPHRASE` can override the selected network profile
- `BALANCE_CHECK_ENABLED` accepts `true/false`, `1/0`, `yes/no`, and `on/off`
- `MINIMUM_BALANCE_XLM` must be a non-negative decimal value

## Usage

Run the CLI:

```bash
python main.py
```

Example flow:

```text
--- Stellar Agent ---
Enter destination public key (or type 'exit' to quit): G...
Enter amount to send (in XLM): 10
Sending 10.0 XLM to G...
Transaction Successful!
Transaction Hash: abc123...
```

## Development

Run the test suite:

```bash
pytest tests/
```

## Contributing

Contributions should include:

- A focused change set
- Tests for new behavior
- Documentation updates when configuration or user-facing behavior changes

Open a pull request with a clear description of the problem, approach, and validation steps.
