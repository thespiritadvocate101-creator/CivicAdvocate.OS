#!/usr/bin/env bash
# ==============================================================================
# Script Name: deploy_sovereign_covenant.sh (Global Termux Prefix Deployment)
# Description: Initializes, hashes, and locks the Sovereign Covenant framework
#              globally within the Termux system prefix.
# ==============================================================================

set -euo pipefail

# Define global paths within the Termux prefix hierarchy
GLOBAL_DIR="${PREFIX}/var/lib/truth_mandate/ledger"
GLOBAL_MANIFEST_DIR="${PREFIX}/share/truth_mandate/manifests"
MISSION_LEDGER="${GLOBAL_DIR}/mission_ledger.jsonl"
COVENANT_MANIFEST="${GLOBAL_MANIFEST_DIR}/sovereign_covenant.md"
GENESIS_PAYLOAD_ID="R00638523"

echo "[*] Initializing Global Termux Prefix Deployment Sequence..."

# Ensure global prefix directory structures exist
mkdir -p "${GLOBAL_DIR}"
mkdir -p "${GLOBAL_MANIFEST_DIR}"

# Remove write permissions globally if previously locked
if [ -f "${MISSION_LEDGER}" ]; then
    echo "[*] Lifting global write lock on existing ledger..."
    chmod 644 "${MISSION_LEDGER}" || true
fi

# Generate SHA-512 cryptographic hash anchor for the covenant deployment
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
HASH_INPUT="${GENESIS_PAYLOAD_ID}:SOVEREIGN_COVENANT:${TIMESTAMP}"
GENESIS_HASH=$(echo -n "${HASH_INPUT}" | sha512sum | awk '{print $1}')

echo "[*] Generated Genesis Anchor Hash: ${GENESIS_HASH}"

# Append deployment event to the global ledger
echo "{\"timestamp\": \"${TIMESTAMP}\", \"event\": \"SOVEREIGN_COVENANT_DEPLOY\", \"payload_id\": \"${GENESIS_PAYLOAD_ID}\", \"genesis_hash\": \"${GENESIS_HASH}\", \"status\": \"ACTIVE\"}" >> "${MISSION_LEDGER}"

# Apply global read-only lock (mode 444: read-only for owner, group, and others globally)
echo "[*] Applying Global Read-Only Lock (444) across Termux prefix..."
chmod 444 "${MISSION_LEDGER}"

echo "[+] Global Sovereign Covenant successfully deployed, hashed, and locked at: ${MISSION_LEDGER}"
