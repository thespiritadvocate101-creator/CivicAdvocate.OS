#!/usr/bin/env bash
set -e

echo "[*] Deploying PayPal Ledger Bridge Module..."

# Run the integration script
python3 paypal_payout_sync.py

# Commit changes to Git
git add paypal_payout_sync.py financial_ledger.json
git commit -m "feat(accounting): add PayPal payout synchronization and local ledger binding"
git push origin main

echo "[+] PayPal Bridge successfully deployed and synchronized."
