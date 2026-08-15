#!/usr/bin/env python3
import sqlite3
import hashlib
import json

DB_NAME = "audit_ledger.db"

def verify_ledger():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Query latest written root rather than static ID
    cursor.execute("SELECT id, payload_sha512 FROM audit_records ORDER BY id DESC LIMIT 1;")
    row = cursor.fetchone()
    if not row:
        print("[!] No genesis records found in audit_records.")
        return
    latest_id, stored_root = row

    target_tables = [
        ("normalized_federal_awards", "award_id"),
        ("normalized_state_expenditures", "payment_date, agency_name, vendor_name, amount"),
        ("normalized_local_rrc", "abstract_id"),
        ("cross_reference_matches", "id")
    ]

    hasher = hashlib.sha512()
    for table_name, order_clause in target_tables:
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY {order_clause};")
        for r in cursor.fetchall():
            hasher.update(json.dumps(r, default=str, sort_keys=True).encode('utf-8'))

    computed_root = hasher.hexdigest()
    conn.close()

    if computed_root == stored_root:
        print(f"[OK] Ledger integrity intact (Record #{latest_id}). Root: {computed_root[:32]}...")
    else:
        print(f"[FAIL] State modification detected against Record #{latest_id}!")
        print(f"  Stored:   {stored_root[:32]}...")
        print(f"  Computed: {computed_root[:32]}...")

if __name__ == "__main__":
    verify_ledger()
