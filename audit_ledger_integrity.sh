#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${DB_NAME:-civic_advocate}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

export PGPASSWORD="${PGPASSWORD:-local_secure_password}"

LOG_PREFIX="[$(date -u +'%Y-%m-%dT%H:%M:%SZ')][LEDGER_AUDIT]"

# Force unaligned, tuples-only mode (-t -A) to suppress headers
query_sql() {
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q -t -A -F '|' -c "$1"
}

compute_sha512() {
    echo -n "$1" | sha512sum | awk '{print $1}'
}

# Fetch all verified tasks from the audit ledger
SEALED_RECORDS=$(query_sql "
    SELECT 
        v.task_id, 
        v.input_hash, 
        v.output_hash, 
        v.zk_proof_digest, 
        t.payload::text
    FROM verification_audit_ledger v
    JOIN task_queue t ON v.task_id = t.id
    WHERE v.schema_validated = TRUE AND v.fact_gate_validated = TRUE;
")

# Clean up empty lines or whitespace
SEALED_RECORDS=$(echo "$SEALED_RECORDS" | sed '/^$/d')

if [[ -z "$SEALED_RECORDS" ]]; then
    echo "$LOG_PREFIX INFO: No verified ledger entries found to audit."
    exit 0
fi

FAILED_COUNT=0
PASSED_COUNT=0

while IFS="|" read -r TASK_ID RECORDED_INPUT_HASH RECORDED_OUTPUT_HASH ZK_DIGEST PAYLOAD; do
    [[ -z "$TASK_ID" ]] && continue

    # Recalculate input payload hash
    RECALC_INPUT_HASH=$(compute_sha512 "$PAYLOAD")

    # Recalculate canonical output payload hash
    CANONICAL_PAYLOAD=$(echo "$PAYLOAD" | jq -c -S '.')
    RECALC_OUTPUT_HASH=$(compute_sha512 "$CANONICAL_PAYLOAD")

    # Check for payload modification or hash mismatch
    MISMATCH_REASONS=""

    if [[ "$RECORDED_INPUT_HASH" != "$RECALC_INPUT_HASH" ]]; then
        MISMATCH_REASONS+="[Input Hash Tampered/Corrupted] "
    fi

    if [[ "$RECORDED_OUTPUT_HASH" != "$RECALC_OUTPUT_HASH" ]]; then
        MISMATCH_REASONS+="[Output Digest Mismatch] "
    fi

    EXPECTED_ZK="zk-sha512:${RECALC_OUTPUT_HASH:0:32}"
    if [[ "$ZK_DIGEST" != "$EXPECTED_ZK" ]]; then
        MISMATCH_REASONS+="[ZK Digest Proof Mismatch] "
    fi

    if [[ -n "$MISMATCH_REASONS" ]]; then
        echo "$LOG_PREFIX CRITICAL ALERT: Task #$TASK_ID Integrity Violation! Details: $MISMATCH_REASONS" >&2
        ((FAILED_COUNT++))
    else
        echo "$LOG_PREFIX OK: Task #$TASK_ID SHA-512 & ZK proof verified."
        ((PASSED_COUNT++))
    fi
done <<< "$SEALED_RECORDS"

if (( FAILED_COUNT > 0 )); then
    echo "$LOG_PREFIX AUDIT FAILED: $FAILED_COUNT tampered/corrupted record(s) detected out of $((PASSED_COUNT + FAILED_COUNT)) total records." >&2
    exit 1
else
    echo "$LOG_PREFIX AUDIT SUCCESS: All $PASSED_COUNT verified ledger entries matched exact SHA-512 state digests."
    exit 0
fi
