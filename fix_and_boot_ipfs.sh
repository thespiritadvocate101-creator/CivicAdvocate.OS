#!/usr/bin/env bash

echo "==================================================="
echo "       PURGING CONFLICTS & SECURING DAEMON         "
echo "==================================================="

# 1. Sever IPFS Telemetry to protect sovereign data
echo "[*] Disabling Kubo telemetry..."
ipfs config Plugins.Plugins.telemetry.Config.Mode off

# 2. Bypass Android mDNS permission restrictions
echo "[*] Disabling local mDNS discovery..."
ipfs config --json Discovery.MDNS.Enabled false

# 3. Resolve Port 8080 collision
echo "[*] Shifting IPFS Gateway to port 8081..."
ipfs config Addresses.Gateway /ip4/127.0.0.1/tcp/8081

# 4. Clear old log and reignite the daemon
echo "[*] Reigniting IPFS daemon..."
rm -f ipfs_node.log
nohup ipfs daemon > ipfs_node.log 2>&1 &

# Allow time for initialization
sleep 5

echo "==================================================="
echo "                  CURRENT LOG                      "
echo "==================================================="
cat ipfs_node.log
