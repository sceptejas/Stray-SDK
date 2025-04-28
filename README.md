# Stray o1 (Python SDK)

A simple agent that connects to the Stellar blockchain and allows sending XLM payments using natural prompt inputs.

Built with:

- [stellar-sdk](https://github.com/StellarCN/py-stellar-base)
- [requests](https://docs.python-requests.org/)

---

## 📂 Project Structure

```
stray/
├── agent.py      # Main agent logic (prompt-based)
├── horizon.py    # Horizon API connection functions
├── payments.py   # Send payments via Stellar network
├── config.py     # API URLs, secret keys, constants
└── README.md     # Project documentation (this file)
```

---

## 🛠️ Installation

First, install the required Python packages:

```bash
pip install stellar-sdk requests
```

---

## ⚙️ Setup

1. Open `config.py`.
2. Replace the placeholders with your real Stellar **testnet** or **mainnet** keys:

```python
HORIZON_URL = "https://horizon-testnet.stellar.org"
NETWORK_PASSPHRASE = "Test SDF Network ; September 2015"

SOURCE_SECRET = "YOUR_SECRET_KEY"        # Your private key
MONITOR_ACCOUNT_ID = "YOUR_PUBLIC_KEY"    # Your public key
DESTINATION_ACCOUNT_ID = ""               # (Leave empty for manual input)
```

> 🔥 You can create and fund a free Stellar testnet account using [Stellar Laboratory Friendbot](https://laboratory.stellar.org/#account-creator?network=test).

---

## 🚀 Running the Agent

Navigate to the project folder:

```bash
cd stellar_agent/
```

Run the agent:

```bash
python agent.py
```

The agent will:

- Prompt you for the **destination account public key**.
- Prompt you for the **amount** of XLM to send.
- Submit the transaction to the Stellar blockchain.
- Print the transaction result or errors.

Example interaction:

```
--- Stellar Agent ---
Enter destination public key (or type 'exit' to quit): GD6WXYZ...
Enter amount to send (in XLM): 5
Sending 5.0 XLM to GD6WXYZ...
👌 Transaction Successful!
Transaction Hash: 57b8bfc10c998b7dc90d9e4ea228d057412fd8e56b...
```

---

## 🧹 Features

- Simple prompt-based flow
- Automatic transaction building and signing
- Supports Stellar Testnet
- Easily extendable for event-based or batch processing

---

## 🚧 Possible Upgrades

- 🌟 Accept natural language commands ("Send 10 XLM to GD6...")
- 🌟 Add account creation flows (Create Account operation)
- 🌟 Support multiple assets (not just native XLM)
- 🌟 Add retry logic for network failures
- 🌟 Deploy agent on AWS EC2 or serverless functions

---

## ✨ License

This project is free and open-source.  
Feel free to use, modify, and share it!

---

## 💬 Contact

Built with ❤️ by [Your Name or GitHub Handle].  
Contributions welcome!

