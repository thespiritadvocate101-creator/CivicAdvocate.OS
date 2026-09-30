#!/usr/bin/env bash
set -euo pipefail

PORT=8080
LOG_FILE="${HOME}/CivicAdvocate.OS/logs/tunnel.log"

mkdir -p "${HOME}/CivicAdvocate.OS/logs"

echo "[+] Starting local Audit API server on port ${PORT}..."
python3 "${HOME}/CivicAdvocate.OS/server.py" > "${HOME}/CivicAdvocate.OS/logs/api_server.log" 2>&1 &
API_PID=$!

cleanup() {
    echo "[!] Shutting down API server (PID ${API_PID})..."
    kill -9 "${API_PID}" 2>/dev/null || true
}
trap cleanup EXIT

sleep 2

echo "[+] Initializing Cloudflare Tunnel on http://127.0.0.1:${PORT}..."
cloudflared tunnel --url "http://127.0.0.1:${PORT}" 2>&1 | tee "${LOG_FILE}"
