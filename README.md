# Stray-SDK v1.1

A lightweight Python CLI tool for sending XLM payments on the Stellar blockchain network.

## 🌟 Stellar Open Source Builder Program

**A three-month open-source builder journey on Stellar. Focused on real, core contributions—no low-effort PRs. $2,000 rewarded every month to validated builders.**

We welcome meaningful contributions that improve the project's functionality, documentation, and user experience.

## Features

* 🚀 Simple interactive CLI for sending Stellar payments
* ✅ Input validation for addresses and amounts
* 🔒 Environment-based configuration for security
* 🧪 Testnet support out of the box

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

Follow the prompts to send payments:

```text
--- Stellar Agent ---
Enter destination public key (or type 'exit' to quit): GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H
Enter amount to send (in XLM): 10
Sending 10 XLM to GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H...
✅ Transaction Successful!
Transaction Hash: abc123...
```

## Example Usage

### Send a Testnet Payment

1. Make sure your `.env` file contains a valid testnet secret key.
2. Run the CLI:

```bash
python main.py
```

3. Enter the destination public key when prompted.
4. Enter the XLM amount.
5. Confirm the transaction result and copy the transaction hash if needed.

### Example Input

```text
Enter destination public key: GXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Enter amount to send (in XLM): 10
```

### Example Output

```text
✅ Transaction Successful!
Transaction Hash: abc123...
```

## Troubleshooting

### Invalid Secret Key

Make sure your Stellar secret key is valid and starts with `S`.

### Invalid Destination Address

The destination address must be a valid Stellar public key and usually starts with `G`.

### Transaction Failed

Check that:

* The source account has enough testnet XLM
* The destination account exists on Stellar testnet
* The amount is greater than zero
* The Horizon testnet URL is correct

### Network Error

If the transaction fails because of a network issue:

* Check your internet connection
* Verify that `HORIZON_URL` is set to `https://horizon-testnet.stellar.org`
* Try again after a few minutes

### Missing Environment Variables

If the CLI cannot load credentials, confirm that your `.env` file includes:

```env
SOURCE_SECRET=YOUR_TESTNET_SECRET_KEY_HERE
MONITOR_ACCOUNT_ID=YOUR_PUBLIC_KEY_HERE
HORIZON_URL=https://horizon-testnet.stellar.org
NETWORK_PASSPHRASE=Test SDF Network ; September 2015
```

## Development

### Running Tests

```bash
pytest tests/
```

### Project Structure

```text
Stray-SDK/
├── stellar_agent/          # Main package
│   ├── cli.py              # CLI interface
│   ├── client.py           # Stellar client
│   ├── config.py           # Configuration
│   └── utils/              # Utilities
├── tests/                  # Tests
├── main.py                 # Entry point
└── requirements.txt        # Dependencies
```

## Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### How to Contribute

1. **Fork the repository**

   ```bash
   git clone https://github.com/yourusername/Stray-SDK.git
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

   * Write clean, readable code
   * Follow existing code style and conventions
   * Add tests for new features
   * Update documentation as needed

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

   * `feat:` for new features
   * `fix:` for bug fixes
   * `docs:` for documentation changes
   * `test:` for test additions/changes
   * `refactor:` for code refactoring

7. **Push to your fork**

   ```bash
   git push origin feature/your-feature-name
   ```

8. **Open a Pull Request**

   * Provide a clear description of your changes
   * Reference any related issues
   * Ensure all tests pass

### Contribution Guidelines

* **Quality over quantity**: Focus on meaningful contributions that add real value
* **Test your code**: All new features should include tests
* **Document your changes**: Update README and code comments as needed
* **One feature per PR**: Keep pull requests focused and manageable
* **Be respectful**: Follow our code of conduct and be kind to other contributors

### Development Tips

* Use Python 3.8 or higher
* Follow PEP 8 style guidelines
* Keep functions small and focused
* Write descriptive variable names
* Add type hints where appropriate

### Getting Help

* Open an issue for bugs or feature requests
* Join discussions in existing issues
* Ask questions in pull request comments

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to learn and build together.

## License

MIT License

## Disclaimer

This tool is for educational purposes. Always test on testnet before using on mainnet.
