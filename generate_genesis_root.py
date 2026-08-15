#!/usr/bin/env python3
import sqlite3
import hashlib
import json
from datetime import datetime, timezone

DB_NAME = "audit_ledger.db"

def generate_genesis_root():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Define target normalized tables and deterministic ordering keys
    target_tables = [
        ("normalized_federal_awards", "award_id"),
        ("normalized_state_expenditures", "payment_date, agency_name, vendor_name, amount"),
        ("normalized_local_rrc", "abstract_id"),
        ("cross_reference_matches", "id")
    ]

    hasher = hashlib.sha512()
    table_manifest = {}

    for table_name, order_clause in target_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        if not cursor.fetchone():
            continue

        cursor.execute(f"SELECT * FROM {table_name} ORDER BY {order_clause};")
        rows = cursor.fetchall()
        table_manifest[table_name] = len(rows)

        for row in rows:
            row_serialized = json.dumps(row, default=str, sort_keys=True)
            hasher.update(row_serialized.encode('utf-8'))

    genesis_sha512 = hasher.hexdigest()
    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = json.dumps({
        "event": "GENESIS_ROOT_VERIFICATION",
        "manifest": table_manifest,
        "unified_sha512": genesis_sha512
    })

    cursor.execute("PRAGMA table_info(audit_records);")
    columns = [col[1] for col in cursor.fetchall()]

    if 'raw_data' in columns:
        cursor.execute("""
            INSERT INTO audit_records (layer, source, timestamp, payload_sha512, raw_data)
            VALUES (?, ?, ?, ?, ?);
        """, ("Unified_Genesis", "CivicAdvocate.OS Integrity Engine", timestamp_utc, genesis_sha512, payload))
    else:
        cursor.execute("""
            INSERT INTO audit_records (layer, source, timestamp, payload_sha512)
            VALUES (?, ?, ?, ?);
        """, ("Unified_Genesis", "CivicAdvocate.OS Integrity Engine", timestamp_utc, genesis_sha512))

    conn.commit()
    conn.close()

    print(f"[+] Genesis Root Computed: {genesis_sha512}")
    print(f"[+] Written to audit_records at {timestamp_utc}")

if __name__ == "__main__":
    generate_genesis_root()
