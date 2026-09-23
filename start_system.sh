#!/usr/bin/env bash
# CivicAdvocate.OS - Automated System Startup Script

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

PYTHON_BIN="/data/data/com.termux/files/usr/bin/python3"
# Explicitly use the discovered absolute path for cloudflared
CLOUDFLARED_BIN="$(/data/data/com.termux/files/usr/share/doc/cloudflared)"

echo "[*] Activating Termux wake lock..."
termux-wake-lock

echo "[*] Starting FastAPI server on port 8089..."
nohup "$PYTHON_BIN" server.py > server.log 2>&1 &
SERVER_PID=$!
echo "[+] Server started with PID: $SERVER_PID"

# Wait 3 seconds for Uvicorn to bind to port 8089
sleep 3

if [ -z "$CLOUDFLARED_BIN" ]; then
    echo "[!] Error: cloudflared binary could not be located."
    exit 1
fi

echo "[*] Starting Cloudflare Tunnel pointing to port 8089 (via $CLOUDFLARED_BIN)..."
nohup "$CLOUDFLARED_BIN" tunnel --url http://localhost:8089 > tunnel.log 2>&1 &
TUNNEL_PID=$!
echo "[+] Tunnel started with PID: $TUNNEL_PID"

echo "--------------------------------------------------------"
echo " CivicAdvocate.OS is running!"
echo " Logs: server.log | tunnel.log"
echo "--------------------------------------------------------"
