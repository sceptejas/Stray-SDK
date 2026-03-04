"""Entry point for Stellar Agent CLI."""
from dotenv import load_dotenv
from stellar_agent.cli import run

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    run()
