import os
import json
import requests
from financial_ledger import FinancialAccountingEngine

class PayPalLedgerBridge:
    def __init__(self, amount, recipient_email, memo="Personal funding draw"):
        self.amount = float(amount)
        self.recipient_email = recipient_email
        self.memo = memo
        self.ledger = FinancialAccountingEngine()
        
        # PayPal API Credentials from environment variables (fallback to sandbox/placeholder if not set)
        self.client_id = os.getenv("PAYPAL_CLIENT_ID", "YOUR_CLIENT_ID")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
        self.api_base = os.getenv("PAYPAL_API_BASE", "https://api-m.sandbox.paypal.com") # Switch to api-m.paypal.com for live

    def execute_local_ledger_draw(self):
        balances = self.ledger.generate_balance_sheet()
        treasury_balance = balances.get("Primary Treasury", 0.0)
        
        if self.amount > treasury_balance:
            print(f"[!] Error: Insufficient treasury balance. Available: ${treasury_balance:,.2f}")
            return False
            
        print(f"[*] Recording local draw of ${self.amount:,.2f} to PayPal Account ({self.recipient_email})...")
        self.ledger.record_transaction(
            account_from="Primary Treasury",
            account_to="PayPal Business Account",
            amount=self.amount,
            memo=self.memo
        )
        print("[+] Local ledger updated and sealed with SHA-512.")
        return True

    def trigger_paypal_api_payout(self):
        if self.client_id == "YOUR_CLIENT_ID":
            print("[*] PayPal API credentials not set in environment. Skipping live API call, but local ledger draw is complete.")
            print("[*] To enable live payouts, set export PAYPAL_CLIENT_ID='...' and PAYPAL_CLIENT_SECRET='...'")
            return
            
        try:
            # 1. Get OAuth Token
            auth_url = f"{self.api_base}/v1/oauth2/token"
            headers = {"Accept": "application/json", "Accept-Language": "en_US"}
            data = {"grant_type": "client_credentials"}
            
            response = requests.post(auth_url, auth=(self.client_id, self.client_secret), headers=headers, data=data)
            if response.status_code != 200:
                print(f"[!] Failed to authenticate with PayPal API: {response.text}")
                return
                
            access_token = response.json().get("access_token")
            
            # 2. Execute Payout Request
            payout_url = f"{self.api_base}/v1/payments/payouts"
            payout_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            payout_payload = {
                "sender_batch_header": {
                    "sender_batch_id": f"civic_draw_{int(os.times()[4])}",
                    "email_subject": "CivicAdvocate.OS Operational & Personal Draw"
                },
                "items": [
                    {
                        "recipient_type": "EMAIL",
                        "amount": {"value": f"{self.amount:.2f}", "currency": "USD"},
                        "receiver": self.recipient_email,
                        "note": self.memo,
                        "sender_item_id": "draw_item_01"
                    }
                ]
            }
            
            p_res = requests.post(payout_url, headers=payout_headers, json=payout_payload)
            if p_res.status_code in [200, 201]:
                print(f"[+] PayPal Payout API request successful: {p_res.json().get('batch_header', {}).get('batch_status')}")
            else:
                print(f"[!] PayPal Payout error: {p_res.text}")
                
        except Exception as e:
            print(f"[!] Error connecting to PayPal API: {e}")

if __name__ == "__main__":
    # Configure draw amount and your PayPal business email here
    DRAW_AMOUNT = 1500.00
    PAYPAL_EMAIL = "thespiritadvocate1.0.1@gmail.com" # Update if using a different business email
    
    bridge = PayPalLedgerBridge(amount=DRAW_AMOUNT, recipient_email=PAYPAL_EMAIL, memo="Personal requirement draw")
    if bridge.execute_local_ledger_draw():
        bridge.trigger_paypal_api_payout()
        bridge.ledger.generate_balance_sheet()

