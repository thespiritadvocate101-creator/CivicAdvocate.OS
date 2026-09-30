#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="audit_summary.json"
PAYLOAD_DIR="./payloads"
TEMP_HASH_LIST=$(mktemp)

cleanup() {
    rm -f "${TEMP_HASH_LIST}"
}
trap cleanup EXIT

for cmd in sha512sum jq; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "[ERROR] Required utility '$cmd' is not installed." >&2
        exit 1
    fi
done

mkdir -p "${PAYLOAD_DIR}"

if [ -z "$(ls -A "${PAYLOAD_DIR}" 2>/dev/null)" ]; then
    echo '<soap:Envelope><Body><AuditQuery id="VEC-001"/></Body></soap:Envelope>' > "${PAYLOAD_DIR}/001_soap_query.xml"
    echo '{"vector": "/api/v1/telemetry", "status": "ACTIVE"}' > "${PAYLOAD_DIR}/002_rest_telemetry.json"
fi

RECORDS_JSON="[]"
RECORD_ID=1

for file in "${PAYLOAD_DIR}"/*; do
    [ -f "$file" ] || continue

    VECTOR_NAME=$(basename "$file")
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    PAYLOAD_HASH=$(sha512sum "$file" | awk '{print $1}')
    STATUS_CODE=200

    echo -n "$PAYLOAD_HASH" >> "${TEMP_HASH_LIST}"

    RECORD=$(jq -n \
        --arg id "REC-$(printf "%04d" "$RECORD_ID")" \
        --arg ts "$TIMESTAMP" \
        --arg vec "/vector/$VECTOR_NAME" \
        --argjson status "$STATUS_CODE" \
        --arg hash "$PAYLOAD_HASH" \
        '{id: $id, timestamp: $ts, vector: $vec, statusCode: $status, payloadHash: $hash}')

    RECORDS_JSON=$(echo "$RECORDS_JSON" | jq --argjson rec "$RECORD" '. + [$rec]')
    RECORD_ID=$((RECORD_ID + 1))
done

if [ -s "${TEMP_HASH_LIST}" ]; then
    MASTER_STATE_ROOT=$(sha512sum "${TEMP_HASH_LIST}" | awk '{print $1}')
else
    MASTER_STATE_ROOT="cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
fi

TOTAL_RECORDS=$((RECORD_ID - 1))
GENERATED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

jq -n \
    --arg masterRoot "$MASTER_STATE_ROOT" \
    --arg genAt "$GENERATED_AT" \
    --argjson total "$TOTAL_RECORDS" \
    --argjson recs "$RECORDS_JSON" \
    '{
        masterStateRoot: $masterRoot,
        generatedAt: $genAt,
        totalRecordsExported: $total,
        records: $recs
    }' > "${OUTPUT_FILE}"
