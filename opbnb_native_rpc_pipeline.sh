#!/usr/bin/env bash
# opbnb_native_rpc_pipeline.sh - Query opBNB via Native JSON-RPC Node

TARGET_ADDRESS="${1:-}"
RPC_URL="https://opbnb-mainnet-rpc.bnbchain.org"

# Validate 42-character EVM address format
if [[ ! "$TARGET_ADDRESS" =~ ^0x[a-fA-F0-9]{40}$ ]]; then
    echo "[!] Error: Invalid EVM address format."
    echo "Usage: ./opbnb_native_rpc_pipeline.sh <0x...>"
    exit 1
fi

echo "[*] Querying opBNB Mainnet Native RPC for: ${TARGET_ADDRESS}"

# 1. Fetch Account Native Balance using standard eth_getBalance
echo -e "\n=== opBNB Balance ==="
BALANCE_PAYLOAD="{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"${TARGET_ADDRESS}\", \"latest\"],\"id\":1}"

# Fetch and extract the hex result using jq
HEX_BALANCE=$(curl -s -X POST "${RPC_URL}" -H "Content-Type: application/json" -d "${BALANCE_PAYLOAD}" | jq -r '.result')

if [[ "$HEX_BALANCE" == "null" || -z "$HEX_BALANCE" ]]; then
    echo "[!] RPC Error: Failed to fetch balance from node."
else
    # Use python3 to safely convert the huge hex string to decimal Wei and standard BNB
    DECIMAL_WEI=$(python3 -c "print(int('${HEX_BALANCE}', 16))")
    DECIMAL_BNB=$(python3 -c "print(f'{(${DECIMAL_WEI} / 10**18):.6f}')")
    
    echo "Wei: ${DECIMAL_WEI}"
    echo "BNB: ${DECIMAL_BNB}"
fi

# 2. Fetch Total Outbound Transactions (Nonce) using eth_getTransactionCount
echo -e "\n=== Total Outbound Transactions ==="
NONCE_PAYLOAD="{\"jsonrpc\":\"2.0\",\"method\":\"eth_getTransactionCount\",\"params\":[\"${TARGET_ADDRESS}\", \"latest\"],\"id\":1}"

HEX_NONCE=$(curl -s -X POST "${RPC_URL}" -H "Content-Type: application/json" -d "${NONCE_PAYLOAD}" | jq -r '.result')

if [[ "$HEX_NONCE" == "null" || -z "$HEX_NONCE" ]]; then
    echo "[!] RPC Error: Failed to fetch transaction count."
else
    DECIMAL_NONCE=$(python3 -c "print(int('${HEX_NONCE}', 16))")
    echo "Count: ${DECIMAL_NONCE}"
fi
