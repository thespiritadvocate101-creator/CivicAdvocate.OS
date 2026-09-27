import hashlib
import json
import sqlite3

def verify_record(db_path: str, record_id: int) -> bool:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT entry_hash, payload FROM audit_ledger WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        
        if not row:
            print(f"Record {record_id} not found.")
            return False
            
        stored_hash, payload_str = row
        payload = json.loads(payload_str)
        
        # Re-serialize with exact same normalization rules
        recalculated_hash = hashlib.sha512(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        
        is_valid = stored_hash == recalculated_hash
        print(f"Record ID: {record_id}")
        print(f"Stored Hash:       {stored_hash}")
        print(f"Recalculated Hash: {recalculated_hash}")
        print(f"Integrity Status:  {'PASS' if is_valid else 'FAIL'}")
        return is_valid

if __name__ == "__main__":
    verify_record("forensic_ledger.db", 1)
