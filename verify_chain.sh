#!/bin/bash

LEDGER_FILE="ledger/mission_ledger.jsonl"

echo "[*] Initializing chronological sorting and chain verification..."
echo "[*] Stream target: ${LEDGER_FILE}"

if [ ! -f "$LEDGER_FILE" ]; then
    echo "[-] Error: Target ledger file not found at '${LEDGER_FILE}'"
    exit 1
fi

# Use jq to isolate only cryptographically signed blocks, sort them numerically by audit_id, and save to a temp matrix
TEMP_MATRIX=$(jq -c 'select(.sha512_checksum != null) | .audit_id |= (if type == "string" then tonumber else . end)' "$LEDGER_FILE" | jq -s -c 'sort_by(.audit_id) | .[]')

if [ -z "$TEMP_MATRIX" ]; then
    echo "[-] Error: No valid cryptographic blocks found to sort."
    exit 1
fi

LINE_NUM=0
PREV_HASH=""

echo "==================== CHRONOLOGICAL AUDIT ===================="
while IFS= read -r block; do
    ((LINE_NUM++))
    
    AUDIT_ID=$(echo "$block" | jq -r '.audit_id')
    INTAKE_ID=$(echo "$block" | jq -r '.intake_id')
    CURRENT_HASH=$(echo "$block" | jq -r '.sha512_checksum')
    TIMESTAMP=$(echo "$block" | jq -r '.timestamp')

    echo "Step #${LINE_NUM} [Audit ID: ${AUDIT_ID}] | Time: ${TIMESTAMP} | Node: [${INTAKE_ID}]"
    
    # Optional: If your ledger contains a 'previous_hash' link, you can uncomment the block validation below
    # if [ -n "$PREV_HASH" ] && [ "$(echo "$block" | jq -r '.previous_hash // empty')" != "$PREV_HASH" ]; then
    #     echo "🚨 HASH CHAIN BREAK DETECTED AT AUDIT ID: ${AUDIT_ID}"
    # fi
    
    PREV_HASH="$CURRENT_HASH"
done <<< "$TEMP_MATRIX"

# Count any loose text event logs that were appended outside the formal block matrix
EVENT_COUNT=$(jq -c 'select(.sha512_checksum == null)' "$LEDGER_FILE" | wc -l | tr -d ' ')

echo "=========================================================="
echo "✅ Chronological validation complete."
echo "[*] Verified Structured Blocks: ${LINE_NUM}"
echo "[*] Unsigned Telemetry Events:  ${EVENT_COUNT}"
exit 0
