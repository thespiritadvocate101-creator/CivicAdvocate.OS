#!/usr/bin/env bash
# ==============================================================================
# CivicAdvocate.OS - Automated GIS Cron Scheduling Script
# ==============================================================================
set -e

SCRIPT_PATH="$(pwd)/build_gis_pipeline.sh"
CRON_SCHEDULE="0 6 * * *"  # Runs daily at 6:00 AM
JOB_ENTRY="$CRON_SCHEDULE /bin/bash $SCRIPT_PATH >> $(pwd)/gis_cron.log 2>&1"

echo "[*] Configuring automated task schedule for GIS pipeline..."

# Check if crontab is available
if ! command -v crontab &> /dev/null; then
    echo "[!] Error: crontab utility is not installed or available in this environment."
    exit 1
fi

# Fetch existing crontab entries (ignore errors if no crontab exists yet)
EXISTING_CRON=$(crontab -l 2>/dev/null || true)

# Check if the job is already registered
if echo "$EXISTING_CRON" | grep -q "build_gis_pipeline.sh"; then
    echo "[+] GIS pipeline crontab entry already exists. Updating schedule..."
    # Remove old entry and append the new one
    NEW_CRON=$(echo "$EXISTING_CRON" | grep -v "build_gis_pipeline.sh")
    {
        echo "$NEW_CRON"
        echo "$JOB_ENTRY"
    } | crontab -
else
    echo "[+] Adding new crontab entry..."
    {
        echo "$EXISTING_CRON"
        echo "$JOB_ENTRY"
    } | crontab -
fi

echo "[+] Successfully scheduled GIS pipeline execution."
echo "[*] Current active crontab entries:"
crontab -l
