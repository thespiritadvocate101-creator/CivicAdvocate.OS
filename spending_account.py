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
