# Stellar Agent

A lightweight Python CLI tool for sending XLM payments on the Stellar blockchain network.

## 🌟 Stellar Open Source Builder Program

**A three-month open-source builder journey on Stellar. Focused on real, core contributions—no low-effort PRs. $2,000 rewarded every month to validated builders.**

We welcome meaningful contributions that improve the project's functionality, documentation, and user experience.

## Features

- 🚀 Simple interactive CLI for sending Stellar payments
- ✅ Input validation for addresses and amounts (Ed25519 cryptographic validation)
- 🔒 Environment-based configuration for security
- 🧪 Testnet support out of the box
- 💰 Balance checking for any Stellar account
- 📜 Transaction history viewer
- 📝 Memo support for exchange deposits
- 🔐 Multi-signature transaction support
- ⚡ Comprehensive error handling with user-friendly messages
- ✨ Precise amount formatting (Decimal-based, no float precision issues)
- 🧪 Extensive test suite with 24 tests covering all features

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stellar-agent.git
cd stellar-agent
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

Create a `.env` file with your Stellar credentials:

```env
SOURCE_SECRET=YOUR_TESTNET_SECRET_KEY_HERE
MONITOR_ACCOUNT_ID=YOUR_PUBLIC_KEY_HERE
HORIZON_URL=https://horizon-testnet.stellar.org
NETWORK_PASSPHRASE=Test SDF Network ; September 2015
```

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

Follow the prompts to use the interactive menu:
```
--- Stellar Agent ---
Options:
  1. Send Payment
  2. Check Balance
  3. View Transaction History
  4. Exit

Select an option (1-4): 1
Enter destination public key: GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H
Enter amount to send (in XLM): 10
Enter memo (optional, max 28 chars, press Enter to skip):
Sending 10 XLM to GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H...
✅ Transaction Successful!
Transaction Hash: abc123...
```

### Check Balance
```python
from stellar_agent.client import StellarClient

client = StellarClient()
balances = client.get_balance("GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H")
print(f"XLM Balance: {balances['native']}")
```

### View Transaction History
```python
from stellar_agent.client import StellarClient

client = StellarClient()
transactions = client.get_transaction_history(
    "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
    limit=10
)
for tx in transactions:
    print(f"Hash: {tx['hash']}, Date: {tx['created_at']}")
```

### Multi-Signature Support
```python
from stellar_agent.client import StellarClient

client = StellarClient()

# Add a signer to your account
response = client.add_signer(
    source_secret="YOUR_SECRET_KEY",
    signer_public_key="SIGNER_PUBLIC_KEY",
    weight=1
)
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
│   └── utils/             # Utilities
├── tests/                 # Tests
├── main.py               # Entry point
└── requirements.txt      # Dependencies
```

## Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### How to Contribute

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/stellar-agent.git
   cd stellar-agent
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

This tool is for educational purposes. Always test on testnet before using on mainnet.
