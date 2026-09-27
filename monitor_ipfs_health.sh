#!/usr/bin/env bash

LOG_FILE="ipfs_health.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
CID="QmQCQY81UQsBLudNYPBwdyPzksHRMqV48cPaRy49ARu5mx"

echo "===================================================" | tee -a "$LOG_FILE"
echo "       CIVICADVOCATE.OS - IPFS HEALTH CHECK         " | tee -a "$LOG_FILE"
echo "       TIMESTAMP: $TIMESTAMP                        " | tee -a "$LOG_FILE"
echo "===================================================" | tee -a "$LOG_FILE"

# 1. Verify Daemon Responsiveness via RPC API
if ipfs id > /dev/null 2>&1; then
    PEER_ID=$(ipfs id -f="<id>")
    echo "[+] DAEMON STATUS: ACTIVE" | tee -a "$LOG_FILE"
    echo "[+] NODE PEER ID : $PEER_ID" | tee -a "$LOG_FILE"
else
    echo "[!] DAEMON STATUS: OFFLINE / UNRESPONSIVE" | tee -a "$LOG_FILE"
    echo "[!] Executing recovery boot script..." | tee -a "$LOG_FILE"
    if [ -x "./fix_and_boot_ipfs.sh" ]; then
        ./fix_and_boot_ipfs.sh
    fi
    exit 1
fi

# 2. Monitor Active Swarm Peers
PEER_COUNT=$(ipfs swarm peers 2>/dev/null | wc -l | tr -d ' ')
echo "[+] ACTIVE SWARM PEERS: $PEER_COUNT" | tee -a "$LOG_FILE"

if [ "$PEER_COUNT" -eq 0 ]; then
    echo "[!] WARNING: Zero connected swarm peers." | tee -a "$LOG_FILE"
elif [ "$PEER_COUNT" -lt 5 ]; then
    echo "[i] NOTICE: Low peer connectivity ($PEER_COUNT peers)." | tee -a "$LOG_FILE"
fi

# 3. Verify Local Pin State for the Covenant CID
if ipfs pin ls "$CID" > /dev/null 2>&1; then
    echo "[+] COVENANT CID  : PINNED ($CID)" | tee -a "$LOG_FILE"
else
    echo "[!] WARNING: Canonical CID ($CID) is not pinned locally." | tee -a "$LOG_FILE"
fi

echo "===================================================" | tee -a "$LOG_FILE"
