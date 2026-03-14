"""Transaction history display utilities."""
from datetime import datetime
from typing import List, Dict, Any

def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return iso_timestamp

def display_transaction_history(transactions: List[Dict[str, Any]], account_id: str) -> None:
    """
    Display transaction history in a formatted table.
    
    Args:
        transactions: List of transaction dictionaries
        account_id: Account ID for context (to show sent/received)
    """
    if not transactions:
        print("\n📭 No transactions found for this account.")
        return
    
    print(f"\n📜 Transaction History for {account_id[:8]}...{account_id[-8:]}")
    print("=" * 100)
    
    for idx, tx in enumerate(transactions, 1):
        status_icon = "✅" if tx.get('successful', True) else "❌"
        print(f"\n{status_icon} Transaction #{idx}")
        print(f"   Hash: {tx['hash'][:16]}...{tx['hash'][-16:]}")
        print(f"   Time: {format_timestamp(tx['created_at'])}")
        print(f"   Ledger: {tx['ledger']}")
        print(f"   Fee: {tx['fee_charged']:.7f} XLM")
        
        # Display operations
        operations = tx.get('operations', [])
        if operations:
            print(f"   Operations ({len(operations)}):")
            for op in operations:
                if op['type'] == 'payment':
                    # Determine if sent or received
                    if op['from'] == account_id:
                        direction = "📤 Sent"
                        counterparty = op['to']
                    else:
                        direction = "📥 Received"
                        counterparty = op['from']
                    
                    print(f"      {direction}: {op['amount']} XLM")
                    print(f"      {'To' if direction == '📤 Sent' else 'From'}: {counterparty[:8]}...{counterparty[-8:]}")
                
                elif op['type'] == 'create_account':
                    print(f"      🆕 Account Created: {op['account'][:8]}...{op['account'][-8:]}")
                    print(f"      Starting Balance: {op['starting_balance']} XLM")
                
                else:
                    print(f"      🔧 {op['type'].replace('_', ' ').title()}")
        else:
            print(f"   Operations: {tx['operation_count']}")
        
        print("   " + "-" * 96)
    
    print("\n" + "=" * 100)

def display_transaction_summary(transactions: List[Dict[str, Any]], account_id: str) -> None:
    """
    Display summary statistics for transactions.
    
    Args:
        transactions: List of transaction dictionaries
        account_id: Account ID for context
    """
    if not transactions:
        return
    
    total_sent = 0.0
    total_received = 0.0
    total_fees = 0.0
    payment_count = 0
    
    for tx in transactions:
        total_fees += tx.get('fee_charged', 0)
        
        for op in tx.get('operations', []):
            if op['type'] == 'payment':
                amount = float(op['amount'])
                if op['from'] == account_id:
                    total_sent += amount
                else:
                    total_received += amount
                payment_count += 1
    
    print("\n📊 Transaction Summary")
    print("=" * 50)
    print(f"Total Transactions: {len(transactions)}")
    print(f"Payment Operations: {payment_count}")
    print(f"Total Sent: {total_sent:.7f} XLM")
    print(f"Total Received: {total_received:.7f} XLM")
    print(f"Total Fees Paid: {total_fees:.7f} XLM")
    print(f"Net Change: {(total_received - total_sent - total_fees):.7f} XLM")
    print("=" * 50)
