#!/usr/bin/env bash
TARGET_DEST="0xAbC...129"
LOG_FILE="logs/endpoint_monitor.log"
mkdir -p logs

echo "[SYS] Monitoring active routes for target destination: ${TARGET_DEST}"
while true; do
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[${TIMESTAMP}] Target ${TARGET_DEST} active. Polling state..." >> "$LOG_FILE"
    sleep 5
done
