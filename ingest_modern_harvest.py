#!/usr/bin/env python3
import json
import subprocess
import re

MANIFEST_FILE = "reconciliation_manifest.json"
DB_NAME = "u0_a540"

def push_harvest_to_db():
    try:
        with open(MANIFEST_FILE, "r") as f:
            manifest = json.load(f)
        
        anchored_entries = manifest.get("anchored_entries", [])
        if not anchored_entries:
            print("[!] No entries found in manifest.")
            return

        sql_statements = []
        for entry in anchored_entries:
            # Extract timestamp from inside the JSON payload or the standard anchor format
            ts_match = re.search(r'"timestamp":\s*"([^"]+)"', entry)
            if not ts_match:
                ts_match = re.search(r'TIMESTAMP:\s*([^\s|]+)', entry)
            
            extracted_at = f"'{ts_match.group(1)}'" if ts_match else "NOW()"
            
            # Escape single quotes for SQL compatibility
            escaped_entry = entry.replace("'", "''")
            
            sql_statements.append(
                f"INSERT INTO municipal_transparency (raw_data, extracted_at, investigation_status) "
                f"VALUES ('{escaped_entry}', {extracted_at}, 'PENDING_REVIEW');"
            )

        # Batch execute statements via stdin to psql
        full_sql = "\n".join(sql_statements)
        process = subprocess.Popen(
            ['psql', '-d', DB_NAME, '-f', '-'], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=full_sql)

        if process.returncode == 0:
            print(f"[✓] SUCCESS: {len(sql_statements)} modern harvest records committed to database '{DB_NAME}'.")
        else:
            print(f"[!] DATABASE ERROR:\n{stderr}")

    except FileNotFoundError:
        print(f"[!] CRITICAL: '{MANIFEST_FILE}' not found.")
    except Exception as e:
        print(f"[!] RUNTIME ERROR: {str(e)}")

if __name__ == "__main__":
    push_harvest_to_db()
