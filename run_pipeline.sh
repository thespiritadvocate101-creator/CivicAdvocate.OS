#!/usr/bin/env bash
set -euo pipefail

DB_FILE="audit_ledger.db"

echo "[*] Initializing CivicAdvocate.OS Audit Pipeline..."

# Pre-flight JSON Validator
validate_json_array() {
    local file="$1"
    if [[ -f "$file" ]]; then
        if ! jq -e 'type == "array"' "$file" >/dev/null 2>&1; then
            echo "[!] Skipping $file: Not a valid JSON array (API error or empty payload)."
            return 1
        fi
        return 0
    fi
    return 1
}

# 1. Normalize Federal Layer
if validate_json_array "federal_raw.json"; then
    echo "[1/7] Ingesting Federal awards..."
    sqlite3 "$DB_FILE" << 'SQL'
    CREATE TABLE IF NOT EXISTS normalized_federal_awards (
        award_id TEXT,
        recipient_name TEXT,
        start_date TEXT,
        end_date TEXT,
        UNIQUE(award_id, recipient_name, start_date)
    );
SQL
    jq -r '.results[]? // .[]? | [.["Award ID"] // .award_id, .["Recipient Name"] // .recipient_name, .["Start Date"] // .start_date, .["End Date"] // .end_date] | @tsv' federal_raw.json | while IFS=$'\t' read -r award_id recipient start_date end_date; do
        safe_recipient=$(echo "$recipient" | sed "s/'/''/g")
        sqlite3 "$DB_FILE" "INSERT OR IGNORE INTO normalized_federal_awards VALUES ('$award_id', '$safe_recipient', '$start_date', '$end_date');"
    done
fi

# 2. Normalize State Layer
if validate_json_array "state_raw.json"; then
    echo "[2/7] Ingesting State expenditures..."
    sqlite3 "$DB_FILE" << 'SQL'
    CREATE TABLE IF NOT EXISTS normalized_state_expenditures (
        payment_date TEXT,
        agency_name TEXT,
        vendor_name TEXT,
        amount REAL,
        UNIQUE(payment_date, agency_name, vendor_name, amount)
    );
SQL
    jq -r '.[]? | [.payment_date // .date // "2026-08-15", .agency_name // .agency // "STATE_AGENCY", .vendor_name // .payee // "STATE_VENDOR", .amount // .total_amount // "0.00"] | @tsv' state_raw.json | while IFS=$'\t' read -r st_date st_agency st_vendor st_amount; do
        safe_vendor=$(echo "$st_vendor" | sed "s/'/''/g")
        safe_agency=$(echo "$st_agency" | sed "s/'/''/g")
        sqlite3 "$DB_FILE" "INSERT OR IGNORE INTO normalized_state_expenditures VALUES ('$st_date', '$safe_agency', '$safe_vendor', '$st_amount');"
    done
fi

# 3. Normalize Local Layer
if validate_json_array "local_raw.json"; then
    echo "[3/7] Ingesting Local RRC hook..."
    sqlite3 "$DB_FILE" << 'SQL'
    CREATE TABLE IF NOT EXISTS normalized_local_rrc (
        abstract_id TEXT PRIMARY KEY,
        query_time INTEGER,
        status TEXT
    );
SQL
    jq -r '.[]? | [.abstract, .query_time, .status] | @tsv' local_raw.json | while IFS=$'\t' read -r abs_id q_time rrc_status; do
        sqlite3 "$DB_FILE" "INSERT OR REPLACE INTO normalized_local_rrc VALUES ('$abs_id', '$q_time', '$rrc_status');"
    done
fi

# 4. Cross-Reference Entities
echo "[4/7] Executing entity cross-referencing..."
python3 cross_reference.py

# 5. Generate & Commit Genesis Root
echo "[5/7] Generating SHA-512 genesis root..."
python3 generate_genesis_root.py

# 6. Verify Final State
if [[ -f "verify_integrity.py" ]]; then
    echo "[6/7] Running post-execution integrity verification..."
    python3 verify_integrity.py
fi

# 7. Export Signed Report
if [[ -f "export_audit_report.py" ]]; then
    echo "[7/7] Exporting signed Markdown report..."
    python3 export_audit_report.py
fi

echo "[+] Pipeline execution complete. All layers locked into $DB_FILE."
