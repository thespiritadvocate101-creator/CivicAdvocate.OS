#!/usr/bin/env bash
set -euo pipefail

DB_FILE="civic_ledger.db"
PRIV_KEY="ed25519_private.pem"
PUB_KEY="ed25519_public.pem"
SIG_FILE="signature.sig"
TMP_HASH="payload.hash"
JSONLD_FILE="ledger_export.jsonld"

GENESIS_HASH=$(printf '0%.0s' {1..128})

check_deps() {
    for cmd in sqlite3 openssl sha512sum awk python3; do
        if ! command -v "$cmd" &>/dev/null; then
            echo "[ERROR] Required binary '$cmd' not found. Install via: pkg install sqlite openssl coreutils python" >&2
            exit 1
        fi
    done
}

init_keys() {
    if [[ ! -f "$PRIV_KEY" || ! -f "$PUB_KEY" ]]; then
        openssl genpkey -algorithm ed25519 -out "$PRIV_KEY" 2>/dev/null
        openssl pkey -in "$PRIV_KEY" -pubout -out "$PUB_KEY" 2>/dev/null
        echo "[KEYS] Generated Ed25519 keypair ($PRIV_KEY, $PUB_KEY)."
    else
        echo "[KEYS] Using existing Ed25519 keypair ($PRIV_KEY, $PUB_KEY)."
    fi
}

init_db() {
    if [[ -f "$DB_FILE" ]]; then
        if ! sqlite3 "$DB_FILE" "PRAGMA table_info(audit_ledger);" | grep -qw "action"; then
            echo "[MIGRATION] Outdated schema detected in '$DB_FILE'. Recreating table..."
            sqlite3 "$DB_FILE" "DROP TABLE IF EXISTS audit_ledger;"
        fi
    fi

    sqlite3 "$DB_FILE" <<'SQL'
CREATE TABLE IF NOT EXISTS audit_ledger (
    sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    entry_hash TEXT NOT NULL
);
SQL
    echo "[DATABASE] SQLite ledger ready at '$DB_FILE'."
}

compute_sha512() {
    printf "%s" "$1" | sha512sum | awk '{print $1}'
}

sign_payload() {
    local p_hash="$1"
    printf "%s" "$p_hash" > "$TMP_HASH"
    openssl pkeyutl -sign -inkey "$PRIV_KEY" -rawin -in "$TMP_HASH" -out "$SIG_FILE" 2>/dev/null
}

verify_signature() {
    local p_hash="$1"
    printf "%s" "$p_hash" > "$TMP_HASH"
    if openssl pkeyutl -verify -pubin -inkey "$PUB_KEY" -rawin -in "$TMP_HASH" -sigfile "$SIG_FILE" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

get_last_hash() {
    local last_hash
    last_hash=$(sqlite3 "$DB_FILE" "SELECT entry_hash FROM audit_ledger ORDER BY sequence_id DESC LIMIT 1;" 2>/dev/null || true)
    if [[ -z "$last_hash" ]]; then
        echo "$GENESIS_HASH"
    else
        echo "$last_hash"
    fi
}

validate_intent() {
    local action="$1"
    local payload="$2"
    local max_bytes=4096

    local payload_bytes=${#payload}
    if (( payload_bytes > max_bytes )); then
        echo "[VIOLATION] Payload size ($payload_bytes B) exceeds limit ($max_bytes B)." >&2
        return 1
    fi

    local p_hash
    p_hash=$(compute_sha512 "$payload")

    if ! verify_signature "$p_hash"; then
        echo "[VIOLATION] Ed25519 signature verification failed." >&2
        return 1
    fi

    return 0
}

record_execution() {
    local action="$1"
    local p_hash="$2"
    local prev_hash
    prev_hash=$(get_last_hash)
    local ts
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    local chain_string="${ts}:${action}:${p_hash}:${prev_hash}"
    local entry_hash
    entry_hash=$(compute_sha512 "$chain_string")

    sqlite3 "$DB_FILE" "INSERT INTO audit_ledger (timestamp, action, payload_hash, previous_hash, entry_hash) VALUES ('$ts', '$action', '$p_hash', '$prev_hash', '$entry_hash');"

    echo "$entry_hash"
}

verify_ledger_integrity() {
    local expected_prev="$GENESIS_HASH"
    local is_corrupt=0

    while IFS="|" read -r seq_id ts action p_hash prev_h entry_h; do
        if [[ -z "$seq_id" ]]; then
            continue
        fi

        if [[ "$prev_h" != "$expected_prev" ]]; then
            echo "[CORRUPT] Sequence $seq_id: Hash chain broken (Previous hash mismatch)."
            is_corrupt=1
            break
        fi

        local recalculated
        recalculated=$(compute_sha512 "${ts}:${action}:${p_hash}:${prev_h}")

        if [[ "$recalculated" != "$entry_h" ]]; then
            echo "[CORRUPT] Sequence $seq_id: Checksum mismatch."
            is_corrupt=1
            break
        fi

        expected_prev="$entry_h"
    done < <(sqlite3 -separator "|" "$DB_FILE" "SELECT sequence_id, timestamp, action, payload_hash, previous_hash, entry_hash FROM audit_ledger ORDER BY sequence_id ASC;")

    if [[ "$is_corrupt" -eq 0 ]]; then
        echo "[AUDIT] Persistent Ledger Integrity Check: PASSED"
        return 0
    else
        echo "[AUDIT] Persistent Ledger Integrity Check: FAILED"
        return 1
    fi
}

export_jsonld() {
    local output_file="${1:-$JSONLD_FILE}"

    python3 - <<PYEOF > "$output_file"
import sqlite3
import json

conn = sqlite3.connect("$DB_FILE")
cursor = conn.cursor()
cursor.execute("SELECT sequence_id, timestamp, action, payload_hash, previous_hash, entry_hash FROM audit_ledger ORDER BY sequence_id ASC;")
rows = cursor.fetchall()

records = []
for row in rows:
    seq_id, ts, action, p_hash, prev_hash, entry_hash = row
    record = {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://schema.org"
        ],
        "id": f"urn:civicadvocate:ledger:entry:{seq_id}",
        "type": ["VerifiableCredential", "AuditLedgerRecord"],
        "issuer": "urn:civicadvocate:node:ed25519:local",
        "issuanceDate": ts,
        "credentialSubject": {
            "id": f"urn:civicadvocate:ledger:sequence:{seq_id}",
            "sequenceId": seq_id,
            "action": action,
            "payloadHash": p_hash,
            "previousHash": prev_hash,
            "entryHash": entry_hash
        },
        "proof": {
            "type": "Ed25519Signature2020",
            "created": ts,
            "verificationMethod": "urn:civicadvocate:key:ed25519_public",
            "proofPurpose": "assertionMethod"
        }
    }
    records.append(record)

print(json.dumps(records, indent=2))
conn.close()
PYEOF

    echo "[JSON-LD] Exported $(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM audit_ledger;") records to '$output_file'."
}

main() {
    check_deps
    init_keys
    init_db

    ACTION="COMMIT_RECORD"
    PAYLOAD='{"abstract_id":"544","county":"Johnson","action":"RECORD_SEAL","status":"VERIFIED"}'

    PAYLOAD_HASH=$(compute_sha512 "$PAYLOAD")
    sign_payload "$PAYLOAD_HASH"

    echo "[PAYLOAD] SHA-512 Digest: $PAYLOAD_HASH"

    if validate_intent "$ACTION" "$PAYLOAD"; then
        ENTRY_HASH=$(record_execution "$ACTION" "$PAYLOAD_HASH")
        echo "[SUCCESS] Intent Executed & Persisted to '$DB_FILE'."
        echo "[SEAL] Entry Hash: $ENTRY_HASH"
    fi

    verify_ledger_integrity
    export_jsonld "$JSONLD_FILE"

    rm -f "$SIG_FILE" "$TMP_HASH"
}

main "$@"
