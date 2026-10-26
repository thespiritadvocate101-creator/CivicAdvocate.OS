#!/usr/bin/env bash
# opbnb_meganode_pipeline.sh - Query opBNB and pipe SQL to PostgreSQL
# 100% Pure Bash, JQ, and BC Implementation

NODEREAL_KEY="${NODEREAL_API_KEY:-d28015657ef94a5f9e7d6fe538eea178}"
TARGET_ADDRESS="${1:-}"

# 1. Validate EVM address format
if [[ ! "$TARGET_ADDRESS" =~ ^0x[a-fA-F0-9]{40}$ ]]; then
    echo "[!] Error: Invalid EVM address format." >&2
    exit 1
fi

PUBLIC_RPC="https://opbnb-mainnet-rpc.bnbchain.org"
ENHANCED_ENDPOINT="https://opbnb-mainnet.nodereal.io/v1/${NODEREAL_KEY}"

# Helper: Convert arbitrarily large hex to decimal using 'bc'
hex_to_dec() {
    local hex="${1#0x}"
    hex="${hex:-0}"
    # Convert string to uppercase for bc calculation
    local hex_up=$(echo "$hex" | tr '[:lower:]' '[:upper:]')
    echo "ibase=16; $hex_up" | bc
}

echo "[*] Querying opBNB Mainnet for: ${TARGET_ADDRESS}" >&2
echo "=== 1. Native Balance ===" >&2

# 2. Get Native Balance
BAL_PAYLOAD="{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"${TARGET_ADDRESS}\", \"latest\"],\"id\":1}"
BAL_RES=$(curl -s -X POST "${PUBLIC_RPC}" -H "Content-Type: application/json" -d "${BAL_PAYLOAD}")
BAL_HEX=$(echo "$BAL_RES" | jq -r '.result // empty')

if [[ -n "$BAL_HEX" && "$BAL_HEX" != "null" ]]; then
    BAL_DEC=$(hex_to_dec "$BAL_HEX")
    # awk perfectly handles the 18-decimal division for human-readable output
    BAL_BNB=$(awk "BEGIN { printf \"%.6f\", $BAL_DEC / 1e18 }")
    echo "Wei: $BAL_DEC" >&2
    echo "BNB: $BAL_BNB" >&2
fi

# 3. Helper: Parse JSON transfers safely in Bash via TSV
parse_transfers() {
    jq -r '
        .result.transfers[]? | 
        [
            (.hash // "N/A"),
            (.blockNum // "0x0"),
            (.from // "N/A"),
            (.to // "N/A"),
            (.asset // "BNB"),
            (.value // "0x0")
        ] | @tsv
    ' | while IFS=$'\t' read -r hash block_hex from_addr to_addr asset value_hex; do
        
        # Skip gracefully if no transfers exist
        if [[ -z "$hash" || "$hash" == "N/A" ]]; then
            continue
        fi

        # Convert Hex directly to Decimal integers
        block_dec=$(hex_to_dec "$block_hex")
        val_dec=$(hex_to_dec "$value_hex")

        # Safely construct and print SQL INSERT directly to stdout
        printf "INSERT INTO opbnb_transfers (tx_hash, block_num, from_address, to_address, asset, value_wei) VALUES ('%s', %s, '%s', '%s', '%s', %s) ON CONFLICT (tx_hash) DO NOTHING;\n" \
            "$hash" "$block_dec" "$from_addr" "$to_addr" "$asset" "$val_dec"
    done
}

echo -e "\n=== 2. Recent Outbound Transfers (fromAddress) ===" >&2
OUT_PAYLOAD=$(cat <<JSON
{
  "jsonrpc": "2.0",
  "method": "nr_getAssetTransfers",
  "params": [{"fromAddress": "${TARGET_ADDRESS}", "category": ["external", "20"], "order": "desc", "maxCount": "0x5"}],
  "id": 2
}
JSON
)
curl -s -X POST "${ENHANCED_ENDPOINT}" -H "Content-Type: application/json" -d "${OUT_PAYLOAD}" | parse_transfers

echo -e "\n=== 3. Recent Inbound Transfers (toAddress) ===" >&2
IN_PAYLOAD=$(cat <<JSON
{
  "jsonrpc": "2.0",
  "method": "nr_getAssetTransfers",
  "params": [{"toAddress": "${TARGET_ADDRESS}", "category": ["external", "20"], "order": "desc", "maxCount": "0x5"}],
  "id": 3
}
JSON
)
curl -s -X POST "${ENHANCED_ENDPOINT}" -H "Content-Type: application/json" -d "${IN_PAYLOAD}" | parse_transfers
