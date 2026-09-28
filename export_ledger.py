import json
import sqlite3

def export_ledger_json(db_path: str = "forensic_ledger.db", output_file: str = "ledger_export.json"):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, ledger_id, entry_hash, entity_id, source_agency, payload, verification_status, created_at FROM audit_ledger ORDER BY id ASC;")
        rows = cursor.fetchall()
        
        ledger_data = []
        for row in rows:
            record = dict(row)
            record['payload'] = json.loads(record['payload'])
            ledger_data.append(record)

    with open(output_file, 'w') as f:
        json.dump(ledger_data, f, indent=2)

    print(f"--- EXPORT COMPLETE: {len(ledger_data)} RECORDS WRITTEN TO {output_file} ---")

if __name__ == "__main__":
    export_ledger_json()
