#!/usr/bin/env bash

MASTER_LEDGER="logs/master_ledger.log"
mkdir -p logs

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "[SYS] Committing cryptographic checksums to master ledger..."

# Extract current SHA-512 checksums
FW_HASH=$(sha512sum logs/firewall_rules.log | awk '{print $1}')
TR_HASH=$(sha512sum logs/liquidation_trace.log | awk'{print $1}')

# Append immutable entry to master ledger
{
    echo "--------------------------------------------------"
    echo "TIMESTAMP: ${TIMESTAMP}"
    echo "LEDGER_ENTRY: CRYPTOGRAPHIC_SEAL"
    echo "firewall_rules.log SHA-512: ${FW_HASH}"
    echo "liquidation_trace.log SHA-512: ${TR_HASH}"
    echo "--------------------------------------------------"
} >> "$MASTER_LEDGER"

echo "[SUCCESS] Master ledger updated successfully: ${MASTER_LEDGER}"
