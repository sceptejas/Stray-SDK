![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Stellar SDK](https://img.shields.io/badge/stellar--sdk-13.2.1-green.svg)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)

# Stray-SDK v1.1

A lightweight, secure Python CLI tool for sending XLM payments on the Stellar blockchain network. Built with the official Stellar SDK, Stray-SDK provides a simple yet powerful interface for Stellar transactions with comprehensive input validation, testnet support, and environment-based security configuration.

## 🌟 Stellar Open Source Builder Program

**A three-month open-source builder journey on Stellar. Focused on real, core contributions—no low-effort PRs. $2,000 rewarded every month to validated builders.**

We welcome meaningful contributions that improve the project's functionality, documentation, and user experience.

## 🚀 Features

- **Simple Interactive CLI**: User-friendly command-line interface for sending Stellar payments
- **Comprehensive Validation**: Input validation for addresses, amounts, and secret keys with detailed error messages
- **Secure Configuration**: Environment-based configuration for sensitive credentials
- **Testnet Support**: Built-in support for Stellar testnet for safe testing
- **Balance Checking**: Optional balance validation before transactions
- **Multi-Signature Support**: Advanced features for multi-signature accounts
- **Error Handling**: Robust error handling and user-friendly feedback

## 📋 Prerequisites

Before installing Stray-SDK, ensure your system meets the following requirements:

### Python Version
- **Python 3.8 or higher** (Recommended: Python 3.9+)
- Check your Python version: `python --version` or `python3 --version`

### Dependencies
- **stellar-sdk 13.2.1** - Official Stellar SDK for Python
- **python-dotenv 1.2.1** - Environment variable management
- **pytest 9.0.2** - Testing framework (for development)

### System Requirements
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 512MB RAM
- **Network**: Internet connection for Stellar network access

## 🛠️ Installation

### Option 1: Clone and Install (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/omolobamoyinoluwa-max/Stray-SDK.git
cd Stray-SDK
```

2. **Create a virtual environment (recommended):**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your Stellar credentials
```

### Option 2: Install as Package

1. **Install directly from repository:**
```bash
pip install git+https://github.com/omolobamoyinoluwa-max/Stray-SDK.git
```

2. **Or install in development mode:**
```bash
git clone https://github.com/omolobamoyinoluwa-max/Stray-SDK.git
cd Stray-SDK
pip install -e .
```

## ⚙️ Configuration

### Environment Variables Setup

Create a `.env` file by copying the example:
```bash
cp .env.example .env
```

Edit the `.env` file with your Stellar credentials:

```env
# Stellar Agent Configuration
# Required: Network Configuration
HORIZON_URL=https://horizon-testnet.stellar.org
NETWORK_PASSPHRASE=Test SDF Network ; September 2015

# Required: Your Stellar Account Credentials 
SOURCE_SECRET=SCYHMQNU7xxxxxxx2SA3QQU2GA27JS6W47VL74JM45IDKDYVIELIRVQQ

# Optional: Account monitoring
MONITOR_ACCOUNT_ID=GBBQHK5UU4xxxxxxxxW4H5ZKCUQRDG25AFJS2IKTAHSL7YPNW6QAU5HC
DESTINATION_ACCOUNT_ID=

# Balance Safety Settings
MINIMUM_BALANCE_XLM=1.0
BALANCE_CHECK_ENABLED=true

# Production Network Settings (Uncomment for mainnet)
# HORIZON_URL=https://horizon.stellar.org
# NETWORK_PASSPHRASE=Public Global Stellar Network ; September 2015
```

### Configuration Options Explained

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SOURCE_SECRET` | ✅ | Your Stellar account secret key (starts with 'S') | `SCYHMQNU7...` |
| `HORIZON_URL` | ✅ | Stellar Horizon API endpoint | `https://horizon-testnet.stellar.org` |
| `NETWORK_PASSPHRASE` | ✅ | Network passphrase for transaction signing | `Test SDF Network ; September 2015` |
| `MONITOR_ACCOUNT_ID` | ❌ | Public key for account monitoring | `GBBQHK5UU4...` |
| `MINIMUM_BALANCE_XLM` | ❌ | Minimum balance to maintain (default: 1.0) | `1.0` |
| `BALANCE_CHECK_ENABLED` | ❌ | Enable balance validation (default: true) | `true` |

### Getting Testnet Credentials

1. **Create a Stellar testnet account:**
   - Visit [Stellar Laboratory](https://laboratory.stellar.org/#account-creator)
   - Click "Create" to generate a new testnet account
   - Save both the public key and secret key

2. **Fund your testnet account:**
   - Use the [Stellar Testnet Faucet](https://friendbot.stellar.org/)
   - Enter your public key to receive 10,000 test XLM

3. **Update your `.env` file:**
   - Add your secret key to `SOURCE_SECRET`
   - Add your public key to `MONITOR_ACCOUNT_ID`

## 🚀 Usage

### Basic Usage

#### Method 1: Run Directly
```bash
python main.py
```

#### Method 2: Use as Package (if installed)
```bash
stellar-agent
```

### Interactive CLI Examples

#### Example 1: Basic Payment
```
--- Stellar Agent ---
Enter destination public key (or type 'exit' to quit): GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H
Enter amount to send (in XLM): 10
Sending 10 XLM to GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H...
✅ Transaction Successful!
Transaction Hash: abc123def456...
```

#### Example 2: Invalid Address Handling
```
--- Stellar Agent ---
Enter destination public key (or type 'exit' to quit): INVALID_ADDRESS
❌ Invalid Stellar address: Address must start with 'G' and be 56 characters long
```

#### Example 3: Insufficient Balance
```
--- Stellar Agent ---
Enter destination public key (or type 'exit' to quit): GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H
Enter amount to send (in XLM): 10000
❌ Insufficient balance: Current balance is 9999.5 XLM, trying to send 10000 XLM
```

### Real-World Usage Scenarios

#### Scenario 1: Micro-Payments for Content
```bash
# Send small amounts for digital content
python main.py
# Destination: GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H
# Amount: 0.5 XLM
```

#### Scenario 2: Batch Testing
```bash
# Test multiple transactions in development
python main.py
# Send various amounts to test accounts
# Monitor transaction hashes for verification
```

#### Scenario 3: Integration Testing
```bash
# Test API integration with known accounts
python main.py
# Use predetermined test accounts for automated testing
```

### Advanced Features

#### Balance Checking
The CLI automatically checks your balance before sending if `BALANCE_CHECK_ENABLED=true`:

```bash
# Balance check output
Current balance: 1000.0 XLM
Minimum balance to maintain: 1.0 XLM
Available to send: 999.0 XLM
```

#### Transaction Verification
After each successful transaction, you can verify it on the Stellar explorer:
- **Testnet**: https://stellar.expert/explorer/testnet/
- **Mainnet**: https://stellar.expert/explorer/public/

### Error Handling

The CLI provides detailed error messages for common issues:

| Error Type | Description | Solution |
|------------|-------------|----------|
| Invalid Address | Address format is incorrect | Ensure address starts with 'G' and is 56 characters |
| Invalid Amount | Amount is not a positive number | Enter a positive decimal number |
| Insufficient Balance | Not enough XLM to complete transaction | Fund your account or reduce amount |
| Network Error | Cannot connect to Stellar network | Check internet connection and Horizon URL |

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

This tool is for educational purposes. Always test on testnet before using on mainnet.`
