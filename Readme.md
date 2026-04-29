# Stray-SDK v1.1

A lightweight Python CLI tool for sending XLM payments on the Stellar blockchain network.

## 🌟 Stellar Open Source Builder Program

**A three-month open-source builder journey on Stellar. Focused on real, core contributions—no low-effort PRs. $2,000 rewarded every month to validated builders.**

We welcome meaningful contributions that improve the project's functionality, documentation, and user experience.

## Features

- 🚀 Simple interactive CLI for sending Stellar payments
- 🔐 **Multi-signature transaction support** - Create and manage multi-signature accounts
- ✅ Input validation for addresses and amounts
- 🔒 Environment-based configuration for security
- 🧪 Testnet support out of the box
- 📝 Comprehensive signature collection workflow

## Installation

1. Clone the repository:
```bash
git clone https://github.com/omolobamoyinoluwa-max/Stray-SDK.git
cd Stray-SDK
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Stellar credentials
```

## Configuration

The application uses environment variables for secure configuration. Copy the example file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your Stellar credentials:

```env
# Required: Network Configuration
HORIZON_URL=https://horizon-testnet.stellar.org
NETWORK_PASSPHRASE=Test SDF Network ; September 2015

# Required: Your Stellar Account Credentials 
SOURCE_SECRET=YOUR_TESTNET_SECRET_KEY_HERE

# Optional: Account monitoring (if applicable)
MONITOR_ACCOUNT_ID=YOUR_PUBLIC_KEY_HERE
DESTINATION_ACCOUNT_ID=

# Balance Safety Settings
MINIMUM_BALANCE_XLM=1.0
BALANCE_CHECK_ENABLED=true

# Multi-Signature Settings
MULTISIG_ENABLED=true
DEFAULT_MULTISIG_THRESHOLD=2
MAX_MULTISIG_SIGNERS=20
```

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `SOURCE_SECRET` | Yes | Your Stellar secret key (56 chars starting with 'S') | - |
| `HORIZON_URL` | No | Stellar Horizon API URL | `https://horizon-testnet.stellar.org` |
| `NETWORK_PASSPHRASE` | No | Stellar network passphrase | `Test SDF Network ; September 2015` |
| `MONITOR_ACCOUNT_ID` | No | Account ID to monitor | - |
| `DESTINATION_ACCOUNT_ID` | No | Default destination account | - |
| `MINIMUM_BALANCE_XLM` | No | Minimum XLM balance to maintain | `1.0` |
| `BALANCE_CHECK_ENABLED` | No | Enable balance checking | `true` |
| `MULTISIG_ENABLED` | No | Enable multi-signature features | `true` |
| `DEFAULT_MULTISIG_THRESHOLD` | No | Default signature threshold for new accounts | `2` |
| `MAX_MULTISIG_SIGNERS` | No | Maximum number of signers allowed | `20` |

## Usage

Run the CLI:
```bash
python main.py
```

Or install as a package:
```bash
pip install -e .
stellar-agent
```

Follow the prompts to send payments:
```
--- Stellar Agent ---
1. Send Single Payment
2. Multi-Signature Operations
3. Exit
Select an option (1-3): 1

--- Stellar Agent ---
Enter destination public key (or type 'exit' to quit): GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H
Enter amount to send (in XLM): 10
Sending 10 XLM to GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H...
✅ Transaction Successful!
Transaction Hash: abc123...
```

## Multi-Signature Support

The SDK now supports comprehensive multi-signature transaction workflows:

### Creating a Multi-Signature Account

```
--- Multi-Signature Operations ---
1. Create Multi-Signature Account
2. Send Multi-Signature Payment
3. Sign Pending Transaction
4. Check Account Signers
5. Back to Main Menu
Select an option (1-5): 1

--- Create Multi-Signature Account ---
Enter master account secret key: [SECRET_KEY]
Add signers (enter 'done' when finished):
Signer 1 public key (or 'done'): GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H
Weight for GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H (1-255): 1
✅ Added signer: GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H (weight: 1)
Signer 2 public key (or 'done'): GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2
Weight for GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2 (1-255): 1
✅ Added signer: GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2 (weight: 1)
Signer 3 public key (or 'done'): done
Enter signature threshold (1-255): 2
Enter starting balance for new account (XLM): 1.0

Creating multi-signature account...
✅ Multi-signature account created successfully!
Account ID: NEW_ACCOUNT_ID
Secret Key: NEW_SECRET_KEY
Threshold: 2
Signers:
  - GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H (weight: 1)
  - GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2 (weight: 1)
```

### Sending Multi-Signature Payments

```
--- Multi-Signature Operations ---
2. Send Multi-Signature Payment

--- Send Multi-Signature Payment ---
Enter multi-signature account ID: MULTISIG_ACCOUNT_ID
Enter destination address: DESTINATION_ADDRESS
Enter amount to send (XLM): 5.0

Building multi-signature transaction...
✅ Transaction built successfully!
Description: Send 5.0 XLM to DESTINATION_ADDRESS
Required signatures: 2
Required signers:
  - GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H
  - GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2

Do you want to sign this transaction now? (y/n): y
Enter your secret key: [SIGNER_SECRET_KEY]
✅ Signature added! Collected: 1/2
⏳ Need 1 more signatures
Share the transaction XDR with other signers to collect their signatures:
[TRANSACTION_XDR]
```

### Signing Pending Transactions

```
--- Multi-Signature Operations ---
3. Sign Pending Transaction

--- Sign Pending Transaction ---
Enter transaction XDR: [TRANSACTION_XDR]
Enter network passphrase (default: Test SDF Network ; September 2015): 
Enter your secret key: [SIGNER_SECRET_KEY]

✅ Signature added successfully!
Source Account: MULTISIG_ACCOUNT_ID
Operations: 1
Transaction ready for submission when 2 signatures are collected
Updated transaction XDR:
[UPDATED_TRANSACTION_XDR]
```

### Checking Account Signers

```
--- Multi-Signature Operations ---
4. Check Account Signers

--- Check Account Signers ---
Enter account ID: ACCOUNT_ID

Account: ACCOUNT_ID
Thresholds: {'low_threshold': 1, 'med_threshold': 2, 'high_threshold': 3}
Signers:
  - GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H (weight: 1)
  - GD5T2U74RZTR55FG3QHRJYGHVQX2D6L6KQD5ZQ2Q2Q2Q2Q2Q2Q2Q2Q2Q2 (weight: 1)
✅ Multi-signature setup is valid
```

## Development

### Running Tests

```bash
pytest tests/
```

### Project Structure

```
stellar-agent/
├── stellar_agent/          # Main package
│   ├── cli.py             # CLI interface
│   ├── client.py          # Stellar client
│   ├── config.py          # Configuration
│   ├── multisig.py        # Multi-signature support
│   └── utils/             # Utilities
│       ├── validators.py  # Input validation
├── tests/                 # Tests
│   ├── test_multisig.py   # Multi-signature tests
│   ├── test_multisig_validators.py # Validator tests
├── main.py               # Entry point
└── requirements.txt      # Dependencies
```

## Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### How to Contribute

1. **Fork the repository**
   ```bash
   git clone https://github.com/omolobamoyinoluwa-max/Stray-SDK.git
   cd Stray-SDK
   ```

2. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up your development environment**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your testnet credentials
   ```

4. **Make your changes**
   - Write clean, readable code
   - Follow existing code style and conventions
   - Add tests for new features
   - Update documentation as needed

5. **Run tests**
   ```bash
   python -m pytest tests/
   ```

6. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```
   
   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/changes
   - `refactor:` for code refactoring

7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Open a Pull Request**
   - Provide a clear description of your changes
   - Reference any related issues
   - Ensure all tests pass

### Contribution Guidelines

- **Quality over quantity**: Focus on meaningful contributions that add real value
- **Test your code**: All new features should include tests
- **Document your changes**: Update README and code comments as needed
- **One feature per PR**: Keep pull requests focused and manageable
- **Be respectful**: Follow our code of conduct and be kind to other contributors

### Good First Issues

Check out issues labeled `good first issue` for beginner-friendly tasks:
- Documentation improvements
- Adding input validation
- Writing tests
- Bug fixes

### Development Tips

- Use Python 3.8 or higher
- Follow PEP 8 style guidelines
- Keep functions small and focused
- Write descriptive variable names
- Add type hints where appropriate

### Getting Help

- Open an issue for bugs or feature requests
- Join discussions in existing issues
- Ask questions in pull request comments

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to learn and build together.

## License

MIT License

## Disclaimer

This tool is for educational purposes. Always test on testnet before using on mainnet.`
