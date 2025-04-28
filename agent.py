from config import SOURCE_SECRET
from payments import send_payment

def prompt_and_send():
    while True:
        print("\n--- Stellar Agent ---")
        destination = input("Enter destination public key (or type 'exit' to quit): ").strip()
        if destination.lower() == "exit":
            break
        
        amount = input("Enter amount to send (in XLM): ").strip()
        
        try:
            amount = float(amount)
            if amount <= 0:
                print("Amount must be positive.")
                continue
        except ValueError:
            print("Invalid amount.")
            continue
        
        print(f"Sending {amount} XLM to {destination}...")
        try:
            response = send_payment(SOURCE_SECRET, destination, amount)
            print("✅ Transaction Successful!")
            print("Transaction Hash:", response['hash'])
        except Exception as e:
            print("❌ Transaction Failed:", str(e))

if __name__ == "__main__":
    prompt_and_send()
