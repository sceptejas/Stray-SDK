# Stray-SDK

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![stellar-sdk](https://img.shields.io/badge/stellar--sdk-13.2.1-brightgreen.svg)](https://pypi.org/project/stellar-sdk/)

A lightweight Python CLI tool for sending XLM payments on the Stellar blockchain network. Built as part of the **Stellar Open Source Builder Program** — a three-month open-source builder journey focused on real, core contributions.

## Prerequisites

- **Python 3.8** or higher
- **pip** (Python package manager)
- A **Stellar testnet account** with a funded secret key (you can create one at [Stellar Laboratory](https://laboratory.stellar.org/#account-creator?network=test))

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sceptejas/Stray-SDK.git
cd Stray-SDK
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Dependencies:**
| Package | Version | Purpose |
|---------|---------|---------|
| `stellar-sdk` | 13.2.1 | Stellar blockchain SDK |
| `python-dotenv` | 1.2.1 | Environment variable management |
| `pytest` | 9.0.2 | Testing framework |

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your Stellar credentials:
```env
# Required
SOURCE_SECRET=YOUR_TESTNET_SECRET_KEY_HERE
HORIZON_URL=https://horizon-testnet.stellar.org
NETWORK_PASSPHRASE=Test SDF Network ; September 2015

# Optional
MONITOR_ACCOUNT_ID=YOUR_PUBLIC_KEY_HERE
DESTINATION_ACCOUNT_ID=
MINIMUM_BALANCE_XLM=1.0
BALANCE_CHECK_ENABLED=true
```

| Variable | Required | Description |
|----------|----------|-------------|
| `SOURCE_SECRET` | Yes | Your 56-character secret key (starts with `S`) |
| `HORIZON_URL` | Yes | Stellar Horizon API endpoint |
| `NETWORK_PASSPHRASE` | Yes | Network identifier string |
| `MINIMUM_BALANCE_XLM` | No | Minimum XLM reserve to maintain (default: `1.0`) |
| `BALANCE_CHECK_ENABLED` | No | Pre-transaction balance validation (default: `true`) |

> **For mainnet**, change `HORIZON_URL` to `https://horizon.stellar.org` and `NETWORK_PASSPHRASE` to `Public Global Stellar Network ; September 2015`.

## Usage

Run the CLI:
```bash
python main.py
```

Or install as a package and run:
```bash
pip install -e .
stellar-agent
```

### Example Session

```
--- Stellar Agent ---
Enter destination public key (or type 'exit' to quit): GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H
Enter amount to send (in XLM): 10

Checking balance...
✅ Sufficient balance: 500.00 XLM available

Sending 10 XLM to GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H...
✅ Transaction Successful!
   Transaction Hash: abc123...
   Ledger: 12345678
```

### Input Validation

The CLI validates all inputs before submitting transactions:
- **Destination address** — must be a valid Stellar public key (56 characters, starts with `G`)
- **Amount** — must be a positive number
- **Balance check** — verifies sufficient funds for payment + fees + minimum reserve

## Features

- Simple interactive CLI for sending Stellar XLM payments
- Input validation for addresses and amounts
- Pre-transaction balance checking with configurable minimum reserve
- Environment-based configuration for security
- Testnet and mainnet support
- Detailed error messages for common failure scenarios

## Development

### Running Tests

```bash
python -m pytest tests/ -v
```

### Project Structure

```
Stray-SDK/
├── stellar_agent/              # Main package
│   ├── __init__.py            # Package metadata
│   ├── cli.py                 # Interactive CLI interface
│   ├── client.py              # Stellar blockchain client
│   ├── config.py              # Configuration management
│   └── utils/
│       └── validators.py      # Input validation utilities
├── tests/                     # Test suite
│   ├── test_validators.py     # Validator & config tests
│   ├── test_client.py         # Client unit tests
│   ├── test_cli.py            # CLI unit tests
│   └── test_cli_integration.py # Integration tests
├── main.py                    # Entry point
├── setup.py                   # Package setup
├── requirements.txt           # Dependencies
└── .env.example               # Environment template
```

## Contributing

We welcome meaningful contributions! See the steps below:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Install dependencies (`pip install -r requirements.txt`)
4. Make your changes and add tests
5. Run the test suite (`python -m pytest tests/`)
6. Commit with conventional messages (`feat:`, `fix:`, `docs:`, `test:`)
7. Push and open a Pull Request

**Guidelines:** One feature per PR. Quality over quantity. All new features should include tests.

### Good First Issues

Check out issues labeled `good first issue` for beginner-friendly tasks.

## License

MIT License

## Disclaimer

This tool is for educational purposes. Always test on testnet before using on mainnet.
