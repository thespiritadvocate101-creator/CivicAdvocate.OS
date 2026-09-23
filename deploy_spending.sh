#!/usr/bin/env bash
set -e

echo "[*] Fixing Financial Ledger and Deploying Spending Account Subsystem..."

# 1. Update Financial Ledger Module with correct syntax
cat << 'EOF_PY' > financial_ledger.py
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
            print(f"[+] Loaded {len(self.transactions)} financial transactions.")
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
        print(f"[+] Recorded transaction {tx_id[:16]}... | ${amount:,.2f} -> {account_to} ({memo})")

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
EOF_PY

# 2. Re-create Spending Account Python Module
cat << 'EOF_PY' > spending_account.py
import json
import os
import sys
from financial_ledger import FinancialAccountingEngine

class SpendingAccountManager:
    def __init__(self, account_name="Operational Spending Account"):
        self.account_name = account_name
        self.ledger_engine = FinancialAccountingEngine()

    def get_account_balance(self):
        balances = self.ledger_engine.generate_balance_sheet()
        return balances.get(self.account_name, 0.0)

    def fund_spending_account(self, amount, source="Primary Treasury"):
        print(f"[*] Transferring ${amount:,.2f} from {source} to {self.account_name}...")
        self.ledger_engine.record_transaction(
            account_from=source,
            account_to=self.account_name,
            amount=amount,
            memo="Operational funding transfer"
        )

    def disburse_expense(self, recipient, amount, category, memo):
        current_balance = self.get_account_balance()
        if amount > current_balance:
            print(f"[!] Error: Insufficient funds in {self.account_name}. Available: ${current_balance:,.2f}, Requested: ${amount:,.2f}")
            return False

        full_memo = f"[{category.upper()}] {memo}"
        print(f"[*] Disbursing ${amount:,.2f} to {recipient} for {category}...")
        
        self.ledger_engine.record_transaction(
            account_from=self.account_name,
            account_to=recipient,
            amount=amount,
            memo=full_memo
        )
        print(f"[+] Disbursement successful. New account balance: ${self.get_account_balance():,.2f}")
        return True

if __name__ == "__main__":
    manager = SpendingAccountManager()
    
    # Ensure operational spending account has funds from Treasury
    balance = manager.get_account_balance()
    if balance <= 0:
        manager.fund_spending_account(5000.00, source="Primary Treasury")
    
    # Record sample operational expenses
    manager.disburse_expense(
        recipient="Cloud Infrastructure Provider", 
        amount=120.00, 
        category="Hosting", 
        memo="Monthly Cloudflare Tunnel & server instance upkeep"
    )
    
    manager.disburse_expense(
        recipient="API Data Services", 
        amount=45.00, 
        category="Data", 
        memo="EPA compliance endpoint query credits"
    )

    # Final balance check
    manager.ledger_engine.generate_balance_sheet()
EOF_PY

# 3. Run the spending account script
python3 spending_account.py

# 4. Commit to Git and push to origin main
git add financial_ledger.py spending_account.py financial_ledger.json
git commit -m "fix(accounting): correct transaction count syntax and finalize spending account integration"
git push origin main

echo "[+] Spending Account subsystem deployed and synchronized successfully."
