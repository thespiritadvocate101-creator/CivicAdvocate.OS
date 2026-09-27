#!/usr/bin/env bash
echo "[*] Initializing CivicAdvocate.OS System Stack..."

# 1. Ensure PostgreSQL is active
pg_ctl status >/dev/null 2>&1 || pg_ctl -D $PREFIX/var/postgres start
echo "[+] PostgreSQL service verified."

# 2. Start Background Task Worker
nohup python pg_task_worker.py > worker.log 2>&1 &
echo "[+] Task Worker daemonized (PID: $!)"

# 3. Start Flask API Node (Port 8086)
nohup python civic_api_node.py > api_node.log 2>&1 &
echo "[+] Flask API Node online on port 8086 (PID: $!)"

# 4. Start Code-Server (Port 8080)
nohup code-server --bind-addr 0.0.0.0:8080 > code_server.log 2>&1 &
echo "[+] Code-Server active on port 8080 (PID: $!)"

# 5. Launch Cloudflare Tunnel for API Node (Port 8086)
nohup cloudflared tunnel --url http://localhost:8086 > tunnel.log 2>&1 &
echo "[+] Cloudflare Tunnel established (PID: $!)"

echo "[*] CivicAdvocate.OS startup sequence complete. Check respective logs for real-time telemetry."
