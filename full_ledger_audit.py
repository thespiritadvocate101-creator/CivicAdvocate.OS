import hashlib
import json
import sqlite3

def run_full_audit(db_path: str = "forensic_ledger.db"):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, entry_hash, payload FROM audit_ledger ORDER BY id ASC;")
        rows = cursor.fetchall()
        
        print(f"--- STARTING LEDGER INTEGRITY SWEEP: {len(rows)} RECORDS ---")
        passed = 0
        failed = 0
        
        for row in rows:
            record_id, stored_hash, payload_str = row
            payload = json.loads(payload_str)
            recalculated_hash = hashlib.sha512(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
            
            if stored_hash == recalculated_hash:
                print(f"[RECORD {record_id}] HASH VERIFIED: PASS")
                passed += 1
            else:
                print(f"[RECORD {record_id}] INTEGRITY MISMATCH: FAIL")
                failed += 1
                
        print(f"--- SWEEP COMPLETE: {passed} PASSED, {failed} FAILED ---")

if __name__ == "__main__":
    run_full_audit()
