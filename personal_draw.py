from financial_ledger import FinancialAccountingEngine

def allocate_personal_funds(amount, memo="Personal living expense allocation"):
    ledger = FinancialAccountingEngine()
    balances = ledger.generate_balance_sheet()
    
    treasury_balance = balances.get("Primary Treasury", 0.0)
    if amount > treasury_balance:
        print(f"[!] Error: Insufficient treasury balance. Available: ${treasury_balance:,.2f}")
        return False
        
    print(f"[*] Disbursing ${amount:,.2f} from Primary Treasury for personal use...")
    ledger.record_transaction(
        account_from="Primary Treasury",
        account_to="Personal Reserve",
        amount=amount,
        memo=memo
    )
    print(f"[+] Personal allocation recorded and cryptographically sealed.")
    ledger.generate_balance_sheet()

if __name__ == "__main__":
    # Example: Allocate 1,500.00 for personal needs (adjust amount as needed)
    allocate_personal_funds(1500.00, memo="Personal necessity draw")
