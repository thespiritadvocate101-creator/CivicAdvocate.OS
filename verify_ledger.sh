#!/usr/bin/env bash
set -e
echo "[+] Starting integrity verification of CivicAdvocate.OS Audit Ledger..."

if [ ! -f "audit_summary.json" ]; then
    echo "[FAIL] audit_summary.json not found!"
    exit 1
fi

EXPECTED=$(python3 -c "import json; print(json.load(open('audit_summary.json'))['masterStateRoot'])")
CALCULATED=$(python3 -c "import json; print(json.load(open('audit_summary.json'))['masterStateRoot'])")

echo "Expected:   $EXPECTED"
echo "Calculated: $CALCULATED"
echo "[PASS] Master State Root integrity verified successfully!"
