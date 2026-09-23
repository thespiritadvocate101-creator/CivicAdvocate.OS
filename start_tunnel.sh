#!/data/data/com.termux/files/usr/bin/bash

# Ensure local HTTP server is active
~/CivicAdvocate.OS/start_report_server.sh

echo "[*] Launching Cloudflare Tunnel on port 8085..."
cloudflared tunnel --url http://localhost:8085
