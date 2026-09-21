import sqlite3

DB_PATH = "audit_ledger.db"

def verify_ledger():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total sealed records count
    cursor.execute("SELECT COUNT(*) FROM epa_audit_ledger;")
    total = cursor.fetchone()[0]
    print(f"Total sealed records in ledger: {total}")
    
    # Compliance status breakdown
    cursor.execute("SELECT compliance_status, COUNT(*) FROM epa_audit_ledger GROUP BY compliance_status;")
    breakdown = cursor.fetchall()
    print("\nCompliance Status Breakdown:")
    for status, count in breakdown:
        print(f"  - {status}: {count}")
        
    # Sample records with SHA-512 digests
    cursor.execute("SELECT frs_id, facility_name, program_system, compliance_status, record_hash FROM epa_audit_ledger LIMIT 5;")
    samples = cursor.fetchall()
    print("\nSample Sealed Entries:")
    for row in samples:
        print(f"  [FRS ID: {row[0]}] {row[1]} ({row[2]}) -> Status: {row[3]}")
        print(f"    SHA-512 Digest: {row[4][:32]}...")
        
    conn.close()

if __name__ == "__main__":
    verify_ledger()
