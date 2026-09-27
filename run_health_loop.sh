#!/usr/bin/env bash

INTERVAL=900  # 15 minutes
PID_FILE="health_loop.pid"
LOG_FILE="health_loop.log"

echo $$ > "$PID_FILE"
echo "[*] IPFS Health Loop initialized (PID: $$)" >> "$LOG_FILE"
echo "[*] Interval set to $INTERVAL seconds (15 minutes)" >> "$LOG_FILE"

while true; do
    if [ -x "./monitor_ipfs_health.sh" ]; then
        ./monitor_ipfs_health.sh
    else
        echo "[!] ERROR: monitor_ipfs_health.sh missing or non-executable." >> "$LOG_FILE"
    fi
    sleep "$INTERVAL"
done
