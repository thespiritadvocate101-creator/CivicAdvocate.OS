#!/usr/bin/env bash
set -euo pipefail

LEDGER_FILE="${HOME}/CivicAdvocate.OS/audit_summary.json"
PAYLOAD_DIR="${HOME}/CivicAdvocate.OS/payloads"

if [ ! -f "${LEDGER_FILE}" ]; then
    echo "[FAIL] Ledger file ${LEDGER_FILE} does not exist."
    exit 1
fi

echo "[+] Starting integrity verification of CivicAdvocate.OS Audit Ledger..."

EXPECTED_ROOT=$(jq -r '.masterStateRoot' "${LEDGER_FILE}")
TEMP_HASH_LIST=$(mktemp)
cleanup() { rm -f "${TEMP_HASH_LIST}"; }
trap cleanup EXIT

# Re-hash current payload directory contents without newlines to match compile_ledger.sh
for file in "${PAYLOAD_DIR}"/*; do
    [ -f "$file" ] || continue
    sha512sum "$file" | awk '{print $1}' | tr -d '\n' >> "${TEMP_HASH_LIST}"
done

# Recompute state root from concatenated payload hashes
ACTUAL_ROOT=$(sha512sum "${TEMP_HASH_LIST}" | awk '{print $1}')

if [ "${EXPECTED_ROOT}" = "${ACTUAL_ROOT}" ]; then
    echo "[PASS] Master State Root verified successfully."
    echo "       Root Digest: ${ACTUAL_ROOT}"
    exit 0
else
    echo "[FAIL] Master State Root mismatch detected!"
    echo "       Expected: ${EXPECTED_ROOT}"
    echo "       Actual:   ${ACTUAL_ROOT}"
    exit 1
fi
