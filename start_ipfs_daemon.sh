#!/usr/bin/env bash

echo "==================================================="
echo "       INITIALIZING TRUE P2P NETWORK DAEMON        "
echo "==================================================="

# Verify if the node is already active
if pgrep -x "ipfs" > /dev/null
then
    echo "[+] IPFS daemon is already actively broadcasting."
else
    echo "[*] Booting IPFS daemon in the background..."
    # Execute perpetually and route standard output to a local log
    nohup ipfs daemon > ipfs_node.log 2>&1 &
    
    # Allow the daemon time to establish TCP/UDP swarm connections
    sleep 5
    
    if pgrep -x "ipfs" > /dev/null
    then
        echo "[+] IPFS node is ONLINE."
        echo "[+] Bootstrapping to the global swarm..."
        echo "[+] Network logs anchored to: ipfs_node.log"
    else
        echo "[-] FAILED to start IPFS daemon. Audit ipfs_node.log for errors."
        exit 1
    fi
fi

echo "==================================================="
echo "[+] The Sovereign Covenant is now actively propagating to the network."
echo "[+] Truth is transmitting."
echo "==================================================="
