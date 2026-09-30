#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEDGER_FILE="${SCRIPT_DIR}/audit_summary.json"

echo "[+] Starting integrity verification of CivicAdvocate.OS Audit Ledger..."

if [[ ! -f "${LEDGER_FILE}" ]]; then
    echo "[FAIL] Ledger file ${LEDGER_FILE} does not exist."
    exit 1
fi

STORED_ROOT=$(jq -r '.masterStateRoot' "${LEDGER_FILE}")

# Calculate payload SHA-512 digest sum across payloads directory
CALCULATED_ROOT=$(find "${SCRIPT_DIR}/payloads" -type f -exec sha512sum {} + 2>/dev/null | sort | sha512sum | awk '{print $1}')

if [[ "${STORED_ROOT}" == "${CALCULATED_ROOT}" ]]; then
    echo "[PASS] Master State Root verified successfully."
    echo "       Root Digest: ${STORED_ROOT}"
    exit 0
else
    echo "[FAIL] Master State Root mismatch!"
    echo "       Expected: ${STORED_ROOT}"
    echo "       Calculated: ${CALCULATED_ROOT}"
    exit 1
fi
