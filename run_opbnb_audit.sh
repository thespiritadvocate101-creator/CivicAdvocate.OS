#!/usr/bin/env bash
# run_opbnb_audit.sh - Cron wrapper to log opBNB transfers to local log

TARGET_ADDR="0x4200000000000000000000000000000000000015"
LOG_FILE="${HOME}/opbnb_audit.log"

echo "=== Audit Run: $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" >> "${LOG_FILE}"
./opbnb_meganode_pipeline.sh "${TARGET_ADDR}" >> "${LOG_FILE}" 2>&1
echo -e "\n" >> "${LOG_FILE}"
