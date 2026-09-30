import os
import json
import sqlite3
import hashlib
import subprocess
from datetime import datetime, timezone

DB_PATH = os.path.expandvars("$PREFIX/etc/sv/civic_soap_sync/audit_ledger.db")
OUTPUT_DIR = "./public"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "audit_summary.json")

def export_ledger():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found at {DB_PATH}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, timestamp, vector, status_code, payload_hash FROM soap_audit_log ORDER BY id DESC LIMIT 100")
    rows = cursor.fetchall()
    
    records = []
    hasher = hashlib.sha512()
    
    for row in rows:
        record = {
            "id": row[0],
            "timestamp": row[1],
            "vector": row[2],
            "statusCode": row[3],
            "payloadHash": row[4]
        }
        records.append(record)
        hasher.update(str(row[4]).encode('utf-8'))

    master_root_hash = hasher.hexdigest()
    
    summary = {
        "@context": "https://schema.civicadvocate.os/contexts/audit.jsonld",
        "type": "AuditVerificationSummary",
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "masterStateRoot": master_root_hash,
        "totalRecordsExported": len(records),
        "records": records
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(summary, f, indent=2)
        
    print(f"[SUCCESS] Audit summary exported to {OUTPUT_FILE}. Master Root: {master_root_hash[:16]}...")
    conn.close()

    # Automatic Git commit and push pipeline
    try:
        repo_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(repo_dir)
        
        subprocess.run(["git", "add", OUTPUT_FILE], check=True)
        
        # Check if changes exist in the staging area
        status_res = subprocess.run(["git", "diff", "--cached", "--quiet"])
        if status_res.returncode != 0:
            timestamp_msg = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            subprocess.run(["git", "commit", "-m", f"chore: update automated audit summary [{timestamp_msg}]"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("[SUCCESS] Audit summary successfully committed and pushed to remote repository.")
        else:
            print("[INFO] No state changes detected in audit summary; skipping commit/push.")
    except Exception as e:
        print(f"[ERROR] Git synchronization failed: {e}")

if __name__ == "__main__":
    export_ledger()
