import json
import os
import time
import hashlib

class FinancialAccountingEngine:
    def __init__(self, ledger_file="financial_ledger.json"):
        self.ledger_file = ledger_file
        self.transactions = []
        self.load_ledger()

    def load_ledger(self):
        if os.path.exists(self.ledger_file):
            with open(self.ledger_file, "r") as f:
                self.transactions = json.load(f)
            print(f"[+] Loaded {len(transactions_count := len(self.transactions))} financial transactions.")
        else:
            print("[+] Initializing new financial ledger file.")

    def record_transaction(self, account_from, account_to, amount, memo):
        timestamp = int(time.time())
        tx_id = hashlib.sha256(f"{account_from}{account_to}{amount}{timestamp}".encode()).hexdigest()
        
        # Double-entry structure
        transaction = {
            "tx_id": tx_id,
            "timestamp": timestamp,
            "account_from": account_from,
            "account_to": account_to,
            "amount": float(amount),
            "memo": memo
        }
        
        # Cryptographic state seal
        tx_string = json.dumps(transaction, sort_keys=True)
        transaction["sha512_seal"] = hashlib.sha512(tx_string.encode()).hexdigest()
        
        self.transactions.append(transaction)
        self.save_ledger()
        print(f"[+] Recorded transaction {tx_id[:16]}... | {amount} -> {account_to} ({memo})")

    def save_ledger(self):
        with open(self.ledger_file, "w") as f:
            json.dump(self.transactions, f, indent=4)

    def generate_balance_sheet(self):
        balances = {}
        for tx in self.transactions:
            sender = tx["account_from"]
            receiver = tx["account_to"]
            amt = tx["amount"]
            
            balances[sender] = balances.get(sender, 0.0) - amt
            balances[receiver] = balances.get(receiver, 0.0) + amt
            
        print("\n--- FINANCIAL BALANCE SHEET ---")
        for acc, bal in balances.items():
            print(f"  {acc}: ${bal:,.2f}")
        print("-------------------------------\n")
        return balances

if __name__ == "__main__":
    ledger = FinancialAccountingEngine()
    
    # Example initial capital or operational funding entry
    if not ledger.transactions:
        ledger.record_transaction("External Capital", "Primary Treasury", 50000.00, "Initial operational funding deposit")
        ledger.record_transaction("Primary Treasury", "GIS Infrastructure", 1500.00, "Mapping and spatial data processing allocation")
        ledger.record_transaction("Primary Treasury", "Audit Operations", 2500.00, "Cadastral and compliance verification fund")

    ledger.generate_balance_sheet()
