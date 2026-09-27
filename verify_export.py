import hashlib
import json
import sqlite3

def verify_export_against_db(db_path: str = "forensic_ledger.db", export_file: str = "ledger_export.json"):
    with open(export_file, 'r') as f:
        exported_records = json.load(f)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, entry_hash FROM audit_ledger ORDER BY id ASC;")
        db_records = dict(cursor.fetchall())

    print(f"--- VERIFYING EXPORT FILE ({len(exported_records)} RECORDS) ---")
    mismatches = 0

    for rec in exported_records:
        rec_id = rec['id']
        exported_hash = rec['entry_hash']
        db_hash = db_records.get(rec_id)

        # Recalculate hash directly from exported payload
        recalculated_hash = hashlib.sha512(json.dumps(rec['payload'], sort_keys=True).encode("utf-8")).hexdigest()

        if exported_hash == db_hash == recalculated_hash:
            print(f"[RECORD {rec_id}] MATCH VERIFIED | Hash: {exported_hash[:16]}...")
        else:
            print(f"[RECORD {rec_id}] MISMATCH DETECTED")
            mismatches += 1

    print(f"--- EXPORT AUDIT COMPLETE: {len(exported_records) - mismatches} MATCHED, {mismatches} MISMATCHES ---")

if __name__ == "__main__":
    verify_export_against_db()
