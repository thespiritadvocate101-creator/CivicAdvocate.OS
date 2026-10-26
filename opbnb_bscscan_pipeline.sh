#!/usr/bin/env bash
# opbnb_bscscan_pipeline.sh - Query opBNB Mainnet via BscScan opBNB API

# Set API Key (Free key from bscscan.com or opbnb.bscscan.com)
BSCSCAN_KEY="${BSCSCAN_API_KEY:-YourApiKeyToken}"
TARGET_ADDRESS="${1:-}"
API_URL="https://api-opbnb.bscscan.com/api"

# 1. Validate EVM address format (42-char hex)
if [[ ! "$TARGET_ADDRESS" =~ ^0x[a-fA-F0-9]{40}$ ]]; then
    echo "[!] Error: Invalid EVM address format."
    echo "Usage: ./opbnb_bscscan_pipeline.sh <0x...>"
    exit 1
fi

echo "[*] Querying opBNB Mainnet (BscScan API) for: ${TARGET_ADDRESS}"

# 2. Native Account Balance
echo -e "\n=== 1. Native Balance ==="
BAL_RES=$(curl -s "${API_URL}?module=account&action=balance&address=${TARGET_ADDRESS}&apikey=${BSCSCAN_KEY}")
BAL_STATUS=$(echo "$BAL_RES" | jq -r '.status')
BAL_WEI=$(echo "$BAL_RES" | jq -r '.result')

if [[ "$BAL_STATUS" == "1" && "$BAL_WEI" != "null" ]]; then
    python3 -c "
wei = int('${BAL_WEI}')
bnb = wei / 10**18
print(f'Wei: {wei}')
print(f'BNB: {bnb:.6f}')
"
else
    echo "[!] Error fetching balance: $(echo "$BAL_RES" | jq -r '.message // "Unknown error"')"
fi

# 3. Normal Transactions (txlist)
echo -e "\n=== 2. Recent Normal Transactions (txlist) ==="
TX_RES=$(curl -s "${API_URL}?module=account&action=txlist&address=${TARGET_ADDRESS}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc&apikey=${BSCSCAN_KEY}")
TX_STATUS=$(echo "$TX_RES" | jq -r '.status')

if [[ "$TX_STATUS" == "1" ]]; then
    echo "$TX_RES" | jq -r '.result[]? | "Hash: \(.hash)\nBlock: \(.blockNumber)\nFrom: \(.from)\nTo: \(.to)\nValue (Wei): \(.value)\nTime: \(.timeStamp | tonumber | strftime("%Y-%m-%d %H:%M:%S"))\n---"'
else
    echo "[!] Message: $(echo "$TX_RES" | jq -r '.result // .message')"
fi

# 4. ERC-20 Token Transfers (tokentx)
echo -e "\n=== 3. Recent ERC-20 Token Transfers (tokentx) ==="
TOKEN_RES=$(curl -s "${API_URL}?module=account&action=tokentx&address=${TARGET_ADDRESS}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc&apikey=${BSCSCAN_KEY}")
TOKEN_STATUS=$(echo "$TOKEN_RES" | jq -r '.status')

if [[ "$TOKEN_STATUS" == "1" ]]; then
    echo "$TOKEN_RES" | jq -r '.result[]? | "Hash: \(.hash)\nToken: \(.tokenSymbol) (\(.tokenName))\nFrom: \(.from)\nTo: \(.to)\nValue: \(.value)\n---"'
else
    echo "[!] Message: $(echo "$TOKEN_RES" | jq -r '.result // .message')"
fi
