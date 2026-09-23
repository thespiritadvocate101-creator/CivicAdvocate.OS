#!/usr/bin/env bash
set -e

echo "[*] Deploying Truth Mandate Blockchain Engine..."

# Run the blockchain script to initialize and mine the first blocks
python3 build_truth_blockchain.py

# Add to git tracking
git add build_truth_blockchain.py truth_mandate_chain.json
git commit -m "feat(blockchain): initialize immutable Truth Mandate Ledger engine and genesis block"
git push origin main

echo "[+] Truth Mandate Blockchain successfully deployed and pushed to origin main."
