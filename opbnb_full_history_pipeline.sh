#!/usr/bin/env bash
# opbnb_full_history_pipeline.sh - Query opBNB Native Balance & Full Historical Txs via NodeReal API

TARGET_ADDRESS="${1:-}"

# NodeReal Public API key / endpoint for opBNB Mainnet
NODEREAL_KEY="${NODEREAL_API_KEY:-e9a05832a81f4f4f9f7831f4864f1412}"
RPC_URL="https://opbnb-mainnet-rpc.bnbchain.org"
ENHANCED_URL="https://opbnb-mainnet.nodereal.io/v1/${NODEREAL_KEY}"

# 1. Validate 42-character EVM address format
if [[ ! "$TARGET_ADDRESS" =~ ^0x[a-fA-F0-9]{40}$ ]]; then
    echo "[!] Error: Invalid EVM address format."
    echo "Usage: ./opbnb_full_history_pipeline.sh <0x...>"
    exit 1
fi

echo "[*] Querying opBNB Mainnet for: ${TARGET_ADDRESS}"

# 2. Fetch Native Account Balance
echo -e "\n=== 1. Native Balance ==="
BAL_PAYLOAD="{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"${TARGET_ADDRESS}\", \"latest\"],\"id\":1}"
BAL_HEX=$(curl -s -X POST "${RPC_URL}" -H "Content-Type: application/json" -d "${BAL_PAYLOAD}" | jq -r '.result')

if [[ "$BAL_HEX" != "null" && -n "$BAL_HEX" ]]; then
    python3 -c "
wei = int('${BAL_HEX}', 16)
bnb = wei / 10**18
print(f'Wei: {wei}')
print(f'BNB: {bnb:.6f}')
"
else
    echo "[!] Failed to fetch balance."
fi

# 3. Fetch Historical Transactions (nr_getTransactionByAddress)
echo -e "\n=== 2. Transaction History (Normal Txs) ==="
TX_PAYLOAD="{\"jsonrpc\":\"2.0\",\"method\":\"nr_getTransactionByAddress\",\"params\":[{\"address\":\"${TARGET_ADDRESS}\",\"page\":1,\"pageSize\":5}],\"id\":2}"

TX_RES=$(curl -s -X POST "${ENHANCED_URL}" -H "Content-Type: application/json" -d "${TX_PAYLOAD}")
TX_ERR=$(echo "$TX_RES" | jq -r '.error.message // empty')

if [[ -n "$TX_ERR" ]]; then
    echo "[!] RPC Notice: ${TX_ERR}"
    echo "[*] Attempting Asset Transfer lookup fallback (nr_getAssetTransfers)..."

    # 4. Fallback to Asset Transfers (ERC-20 + Native Transfers)
    XFER_PAYLOAD="{\"jsonrpc\":\"2.0\",\"method\":\"nr_getAssetTransfers\",\"params\":[{\"address\":\"${TARGET_ADDRESS}\",\"category\":[\"external\",\"erc20\"],\"maxCount\":\"0x5\"}],\"id\":3}"
    XFER_RES=$(curl -s -X POST "${ENHANCED_URL}" -H "Content-Type: application/json" -d "${XFER_PAYLOAD}")

    echo "$XFER_RES" | jq -r '.result.transfers[]? | "Hash: \(.hash)\nFrom: \(.from)\nTo: \(.to)\nAsset: \(.asset // "BNB")\nValue: \(.value)\n---"'
else
    echo "$TX_RES" | jq -r '.result.list[]? | "Hash: \(.hash)\nBlock: \(.blockNumber)\nFrom: \(.from)\nTo: \(.to)\nValue (Wei): \(.value)\n---"'
fi
