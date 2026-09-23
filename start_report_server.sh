#!/data/data/com.termux/files/usr/bin/bash

PORT=8085
REPORT_DIR="$HOME/CivicAdvocate.OS/audit_reports"

mkdir -p "$REPORT_DIR"

# Kill any existing instance running on port 8085
fuser -k ${PORT}/tcp >/dev/null 2>&1

echo "[*] Starting Python HTTP Server on port ${PORT}..."
python3 -m http.server ${PORT} --directory "$REPORT_DIR" > ~/audit_server.log 2>&1 &
