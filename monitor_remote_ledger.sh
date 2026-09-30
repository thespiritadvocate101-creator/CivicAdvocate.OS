#!/usr/bin/env bash
set -euo pipefail

# Ensure standard PATH for cron / Termux execution environments
PATH="/data/data/com.termux/files/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

ENDPOINT_URL="https://thespiritadvocate101-creator.github.io/CivicAdvocate.OS/ledger_export.jsonld"
LOG_FILE="remote_ledger_monitor.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Fetch JSON-LD payload
TEMP_JSON=$(mktemp)
trap 'rm -f "$TEMP_JSON"' EXIT

if ! curl -sS --fail --max-time 15 "$ENDPOINT_URL" -o "$TEMP_JSON"; then
    log_message "[CRITICAL] HTTP GET failed for endpoint: $ENDPOINT_URL"
    exit 1
fi

# Run cryptographic audit against fetched ledger
AUDIT_OUTPUT=$(python3 - <<PYEOF 2>&1
import sys, json, hashlib

try:
    with open("$TEMP_JSON", "r") as f:
        records = json.load(f)
except Exception as e:
    print(f"JSON PARSE ERROR: {e}")
    sys.exit(2)

expected_prev = "0" * 128
all_valid = True

for rec in records:
    subj = rec.get("credentialSubject", {})
    seq = subj.get("sequenceId")
    ts = rec.get("issuanceDate")
    action = subj.get("action")
    p_hash = subj.get("payloadHash")
    prev_hash = subj.get("previousHash")
    entry_hash = subj.get("entryHash")

    if prev_hash != expected_prev:
        print(f"CORRUPT: Sequence {seq} broken chain link. Expected {expected_prev[:16]}... got {prev_hash[:16]}...")
        all_valid = False
        break

    chain_str = f"{ts}:{action}:{p_hash}:{prev_hash}".encode("utf-8")
    calc_hash = hashlib.sha512(chain_str).hexdigest()

    if calc_hash != entry_hash:
        print(f"CORRUPT: Sequence {seq} hash mismatch. Computed {calc_hash[:16]}... recorded {entry_hash[:16]}...")
        all_valid = False
        break

    expected_prev = entry_hash

if all_valid:
    print(f"OK: {len(records)} entries verified successfully.")
    sys.exit(0)
else:
    sys.exit(1)
PYEOF
)

STATUS=$?

if [ $STATUS -eq 0 ]; then
    log_message "[AUDIT PASSED] $AUDIT_OUTPUT"
else
    log_message "[AUDIT FAILED] $AUDIT_OUTPUT"
    # Optional notification or alert integration can be triggered here
    exit 1
fi
