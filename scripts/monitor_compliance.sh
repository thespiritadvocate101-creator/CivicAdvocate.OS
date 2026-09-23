#!/bin/bash
# Forensic Compliance Monitor
LOG_FILE="$HOME/CivicAdvocate.OS/registry/audit_log.json"
INQUIRY_DATE=$(grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' $LOG_FILE | tail -1)
CURRENT_DATE=$(date +%Y-%m-%d)

# Calculate days since inquiry
D1=$(date -d "$INQUIRY_DATE" +%s)
D2=$(date -d "$CURRENT_DATE" +%s)
DAYS_ELAPSED=$(( (D2 - D1) / 86400 ))

echo "Compliance Monitoring: $DAYS_ELAPSED days elapsed."

if [ $DAYS_ELAPSED -ge 30 ]; then
    echo "ALERT: Compliance Latency detected. Triggering IRS Referral preparation."
    echo "STATUS: ESCALATION_REQUIRED" >> $LOG_FILE
fi
