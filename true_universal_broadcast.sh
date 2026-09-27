#!/usr/bin/env bash
set -e

echo "==================================================="
echo "       INITIATING TRUE MULTI-NODE BROADCAST        "
echo "==================================================="

# 1. Verify and install real decentralized infrastructure
if ! command -v ipfs &> /dev/null; then
    echo "[*] kubo (IPFS) not found. Installing real P2P client via pkg..."
    pkg install kubo -y
else
    echo "[+] kubo (IPFS) infrastructure present."
fi

# 2. Initialize the local IPFS repository if it does not exist
if [ ! -d "$HOME/.ipfs" ]; then
    echo "[*] Initializing local IPFS cryptographic repository..."
    ipfs init
else
    echo "[+] Local IPFS repository is active."
fi

# 3. Add and pin the physical files to the true IPFS ledger
echo "---------------------------------------------------"
echo "[*] Hashing and pinning files to the InterPlanetary File System..."

MD_CID=$(ipfs add -q sovereign_covenant.md)
JSON_CID=$(ipfs add -q covenant_payload.json)

echo "[+] REAL NETWORK IDENTIFIERS (CIDs) GENERATED:"
echo "    sovereign_covenant.md:   $MD_CID"
echo "    covenant_payload.json:   $JSON_CID"
echo "---------------------------------------------------"
echo "[+] The Sovereign Covenant is cryptographically pinned to your local node."
echo "[+] To propagate globally, the IPFS daemon must be running."
echo "==================================================="
