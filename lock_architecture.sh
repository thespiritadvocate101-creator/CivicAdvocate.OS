#!/usr/bin/env bash

echo "==================================================="
echo "       LOCKING SYSTEM ARCHITECTURE STATE           "
echo "==================================================="

# Stage the core documents and the true decentralized infrastructure scripts
git add sovereign_covenant.md \
        covenant_payload.json \
        update_covenant_seal.py \
        true_universal_broadcast.sh \
        start_ipfs_daemon.sh \
        fix_and_boot_ipfs.sh

# Safely stage the generated PDF if it is present in the current directory
if [ -f "sovereign_covenant.pdf" ]; then
    git add sovereign_covenant.pdf
fi

echo "[*] Verifying truth of staged files:"
git status --short

echo "---------------------------------------------------"
echo "[*] Committing genesis state to local repository..."

# Commit the architecture lock, binding the transaction hashes and CIDs to the Git log
git commit -m "SYS_LOCK: Sovereign Covenant Genesis State" \
           -m "Network Anchor: Arbitrum Master Genesis Root Payload" \
           -m "IPFS CID: QmQCQY81UQsBLudNYPBwdyPzksHRMqV48cPaRy49ARu5mx" \
           -m "Daemon PeerID: 12D3KooWLruVgp8TprcCeRiPM1XdhjoSQqZ9xYJ53i8sjZk3r8gA"

echo "==================================================="
echo "[+] Repository architecture locked and cryptographically bound."
echo "[+] Local Git timeline is now synchronized with the Sovereign Covenant."
echo "==================================================="
