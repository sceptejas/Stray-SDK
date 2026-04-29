# Stray-SDK v1.1

A lightweight Python CLI tool for sending XLM payments on the Stellar blockchain network.

## 🌟 Stellar Open Source Builder Program

**A three-month open-source builder journey on Stellar. Focused on real, core contributions—no low-effort PRs. $2,000 rewarded every month to validated builders.**

We welcome meaningful contributions that improve the project's functionality, documentation, and user experience.

## Features

- 🚀 Simple interactive CLI for sending Stellar payments
- ✅ Input validation for addresses and amounts
- 🔒 Environment-based configuration for security
- 🧪 Testnet support out of the box
- 🔑 **Multi-signature (M-of-N) transaction support** — build, co-sign, and submit transactions that require multiple parties to authorise

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

On startup you will see:
```
╔══════════════════════════════════╗
║       Stellar Agent CLI          ║
╚══════════════════════════════════╝
1. Standard payment (single signature)
2. Multi-signature payment
3. Exit
```

### Standard Payment

Select option **1** and follow the prompts:
```
--- Stellar Agent ---
Enter destination public key (or type 'exit' to quit): GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H
Enter amount to send (in XLM): 10
Sending 10 XLM to GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H...
✅ Transaction Successful!
Transaction Hash: abc123...
```

### Multi-Signature Payment

> **Prerequisites:** The source account must have multisig thresholds configured on-chain first.  See the [Python API](#python-api) section below to call `configure_multisig_account()`.

Select option **2** and follow the prompts:
```
--- Stellar Agent · Multi-Sig Payment ---
Enter destination public key (or 'exit' to quit): GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H
Enter amount to send (in XLM): 50
Enter an optional memo (press Enter to skip): Q2 payment

Enter co-signer secret keys one at a time.
Press Enter with no input when done.

Co-signer 1 secret key (or Enter to finish): SCOSIGNERSECRETKEY...
Co-signer 2 secret key (or Enter to finish): 

🔨 Building multi-sig transaction: 50.0 XLM → GBRP...OX2H ...
✅ Transaction built with 2 signature(s).

Show XDR for additional offline signing? (y/N): N
Submit transaction with 2 signature(s)? (y/N): y
✅ Multi-Sig Transaction Successful!
Transaction Hash: def456...
```

#### How multi-sig works (3-step flow)

The `MultiSigClient` supports an **asynchronous pass-around signing** pattern, meaning co-signers do not need to be online simultaneously:

1. **Initiator** calls `build_multisig_payment()` → receives a base-64 XDR string.
2. **Each co-signer** receives the XDR (via email, API, etc.) and calls `sign_transaction()` → returns updated XDR with one more signature.
3. **Anyone** calls `submit_transaction(xdr)` once enough signatures are collected.

### Python API

```python
from stellar_agent.multisig import MultiSigClient

client = MultiSigClient()

# 1. (One-time) Configure the account for 2-of-2 multisig
client.configure_multisig_account(
    source_secret="SA...",                  # master key
    co_signer_public_keys=["GB...", "GC..."],
    signer_weight=1,
    low_threshold=2, med_threshold=2, high_threshold=2,
)

# 2. Build and sign by initiator + any immediately-available co-signers
xdr = client.build_multisig_payment(
    source_secret="SA...",
    destination_public="GD...",
    amount=100,
    signers=["SCOSIGNER1...", "SCOSIGNER2..."],  # optional inline signers
    memo="Invoice #42",
)

# 3. Optionally add more signatures later (pass-around workflow)
xdr = client.sign_transaction(xdr, signer_secret="SLATECOSIGNER...")

# 4. Inspect before submitting
print(client.count_signatures(xdr))   # → 3
print(client.get_thresholds("GSOURCE..."))
# → {'low_threshold': 2, 'med_threshold': 2, 'high_threshold': 2}

# 5. Submit
result = client.submit_transaction(xdr)
print(result["hash"])
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
│   ├── cli.py             # CLI interface (standard + multi-sig modes)
│   ├── client.py          # Single-sig Stellar client
│   ├── config.py          # Configuration
│   ├── multisig.py        # ✨ Multi-signature client (new)
│   └── utils/             # Utilities
├── tests/
│   ├── test_client.py     # Tests for StellarClient
│   └── test_multisig.py   # ✨ 31 tests for MultiSigClient (new)
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
