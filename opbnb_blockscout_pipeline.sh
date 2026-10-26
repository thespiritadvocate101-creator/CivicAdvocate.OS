#!/usr/bin/env bash
# opbnb_blockscout_pipeline.sh - Query and parse opBNB data via Blockscout API

BLOCKSCOUT_KEY="${BLOCKSCOUT_API_KEY:-proapi_demo}"
TARGET_ADDRESS="${1:-}"
MAINNET_CHAINID="204"

# Validate that the provided argument is a valid 42-character EVM address
if [[ ! "$TARGET_ADDRESS" =~ ^0x[a-fA-F0-9]{40}$ ]]; then
    echo "[!] Error: Invalid EVM address format. Please provide a valid 42-character hex address."
    echo "Usage: ./opbnb_blockscout_pipeline.sh <0x...>"
    exit 1
fi

echo "[*] Querying opBNB Mainnet (Chain ${MAINNET_CHAINID}) for: ${TARGET_ADDRESS}"

# 1. Fetch Account Native Balance
echo -e "\n=== opBNB Balance (Wei) ==="
BALANCE_RES=$(curl -s "https://api.blockscout.com/v2/api?chainid=${MAINNET_CHAINID}&module=account&action=balance&address=${TARGET_ADDRESS}&apikey=${BLOCKSCOUT_KEY}")

# Check the API status flag before parsing the result
BALANCE_STATUS=$(echo "$BALANCE_RES" | jq -r '.status')
if [ "$BALANCE_STATUS" != "1" ]; then
    echo "[!] API Error: $(echo "$BALANCE_RES" | jq -r '.message')"
else
    echo "$BALANCE_RES" | jq -r '.result'
fi

# 2. Fetch Latest 5 Transactions
echo -e "\n=== Latest 5 Transactions ==="
TX_RES=$(curl -s "https://api.blockscout.com/v2/api?chainid=${MAINNET_CHAINID}&module=account&action=txlist&address=${TARGET_ADDRESS}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc&apikey=${BLOCKSCOUT_KEY}")

TX_STATUS=$(echo "$TX_RES" | jq -r '.status')
if [ "$TX_STATUS" != "1" ]; then
    # Blockscout often returns status "0" with message "No transactions found" for fresh wallets
    echo "[!] API Message: $(echo "$TX_RES" | jq -r '.message')"
else
    echo "$TX_RES" | jq -r '.result[]? | "Hash: \(.hash)\nTime: \(.timeStamp | tonumber | strftime("%Y-%m-%d %H:%M:%S"))\nValue: \(.value)\n---"'
fi
