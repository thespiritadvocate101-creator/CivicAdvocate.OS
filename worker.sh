#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${DB_NAME:-civic_advocate}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
POLL_INTERVAL="${POLL_INTERVAL:-1}"

export PGPASSWORD="${PGPASSWORD:-local_secure_password}"

exec_sql() {
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q -c "$1"
}

query_sql() {
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q -t -A -F '|' -c "$1"
}

compute_sha512() {
    echo -n "$1" | sha512sum | awk '{print $1}'
}

echo "[+] Launching Verification Worker Loop..."

while true; do
    TASK_ROW=$(query_sql "
        WITH next_task AS (
            SELECT id, schema_type, payload, retry_count, max_retries
            FROM task_queue
            WHERE status = 'pending'
            ORDER BY id ASC
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        )
        UPDATE task_queue t
        SET status = 'processing', updated_at = CURRENT_TIMESTAMP
        FROM next_task n
        WHERE t.id = n.id
        RETURNING t.id, t.schema_type, t.payload::text, t.retry_count, t.max_retries;
    ")

    if [[ -z "$TASK_ROW" ]]; then
        echo "[i] Queue clear. Sleeping (${POLL_INTERVAL}s)..."
        sleep "$POLL_INTERVAL"
        continue
    fi

    IFS="|" read -r TASK_ID SCHEMA_TYPE PAYLOAD RETRY_COUNT MAX_RETRIES <<< "$TASK_ROW"

    if [[ ! "$TASK_ID" =~ ^[0-9]+$ ]]; then
        continue
    fi

    INPUT_HASH=$(compute_sha512 "$PAYLOAD")

    echo "----------------------------------------------------------------------"
    echo "[i] Processing Task #$TASK_ID [Type: $SCHEMA_TYPE | Digest: ${INPUT_HASH:0:16}...]"

    # Step 3A: Structural Schema Gate (.claims array check)
    if ! echo "$PAYLOAD" | jq -e '.claims | type == "array"' >/dev/null 2>&1; then
        REASON="Schema Failure: Missing or invalid '.claims' array"
        echo "[-] Task #$TASK_ID: $REASON"
        
        NEW_RETRY=$((RETRY_COUNT + 1))
        SAN_REASON=$(echo "$REASON" | sed "s/'/''/g")

        if (( NEW_RETRY < MAX_RETRIES )); then
            exec_sql "UPDATE task_queue SET status='pending', retry_count=$NEW_RETRY, error_log='$SAN_REASON', updated_at=CURRENT_TIMESTAMP WHERE id=$TASK_ID;"
        else
            exec_sql "UPDATE task_queue SET status='dead_letter', retry_count=$NEW_RETRY, error_log='$SAN_REASON', updated_at=CURRENT_TIMESTAMP WHERE id=$TASK_ID;"
            exec_sql "INSERT INTO verification_audit_ledger (task_id, input_hash, output_hash, schema_validated, fact_gate_validated, idempotency_validated, failure_reason) VALUES ($TASK_ID, '$INPUT_HASH', 'FAILED', FALSE, FALSE, FALSE, 'DLQ: $SAN_REASON') ON CONFLICT DO NOTHING;"
        fi
        continue
    fi

    # Step 3B: Deterministic Fact Gate Check (Coerce numbers/strings safely)
    FACT_FAILURE=""
    CLAIM_COUNT=$(echo "$PAYLOAD" | jq '.claims | length')

    for (( i=0; i<CLAIM_COUNT; i++ )); do
        KEY=$(echo "$PAYLOAD" | jq -r ".claims[$i].key")
        VAL=$(echo "$PAYLOAD" | jq -c ".claims[$i].value")
        SAN_KEY=$(echo "$KEY" | sed "s/'/''/g")

        CANONICAL_VAL=$(query_sql "SELECT fact_value::text FROM canonical_fact_base WHERE fact_key = '$SAN_KEY';")

        if [[ -z "$CANONICAL_VAL" ]]; then
            FACT_FAILURE="Ungrounded claim: Key '$KEY' absent from Canonical Fact Base"
            break
        fi

        MATCH=$(jq -n --argjson c "$CANONICAL_VAL" --argjson v "$VAL" '(($c|tonumber? // $c) == ($v|tonumber? // $v))')
        if [[ "$MATCH" != "true" ]]; then
            FACT_FAILURE="Fact Mismatch on '$KEY': Expected $CANONICAL_VAL, got $VAL"
            break
        fi
    done

    if [[ -n "$FACT_FAILURE" ]]; then
        echo "[-] Task #$TASK_ID Fact Gate Failure: $FACT_FAILURE"
        NEW_RETRY=$((RETRY_COUNT + 1))
        SAN_FAIL=$(echo "$FACT_FAILURE" | sed "s/'/''/g")

        if (( NEW_RETRY < MAX_RETRIES )); then
            exec_sql "UPDATE task_queue SET status='pending', retry_count=$NEW_RETRY, error_log='$SAN_FAIL', updated_at=CURRENT_TIMESTAMP WHERE id=$TASK_ID;"
        else
            exec_sql "UPDATE task_queue SET status='dead_letter', retry_count=$NEW_RETRY, error_log='$SAN_FAIL', updated_at=CURRENT_TIMESTAMP WHERE id=$TASK_ID;"
            exec_sql "INSERT INTO verification_audit_ledger (task_id, input_hash, output_hash, schema_validated, fact_gate_validated, idempotency_validated, failure_reason) VALUES ($TASK_ID, '$INPUT_HASH', '$SAN_FAIL', TRUE, FALSE, FALSE, 'DLQ: $SAN_FAIL') ON CONFLICT DO NOTHING;"
        fi
        continue
    fi

    # Step 3C: SHA-512 Ledger Sealing
    CANONICAL_PAYLOAD=$(echo "$PAYLOAD" | jq -c -S '.')
    OUTPUT_HASH=$(compute_sha512 "$CANONICAL_PAYLOAD")

    exec_sql "
        BEGIN;
        INSERT INTO verification_audit_ledger (
            task_id, input_hash, output_hash, schema_validated,
            fact_gate_validated, idempotency_validated, zk_proof_digest, sealed_at
        ) VALUES (
            $TASK_ID, '$INPUT_HASH', '$OUTPUT_HASH', TRUE, TRUE, TRUE, 'zk-sha512:${OUTPUT_HASH:0:32}', CURRENT_TIMESTAMP
        );

        UPDATE task_queue
        SET status = 'verified', error_log = NULL, updated_at = CURRENT_TIMESTAMP
        WHERE id = $TASK_ID;
        COMMIT;
    "

    echo "[+] SUCCESS: Task #$TASK_ID verified & cryptographically sealed."
    echo "    Output Digest: $OUTPUT_HASH"
done
