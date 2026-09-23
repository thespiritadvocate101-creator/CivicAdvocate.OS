import os
import sys
import sqlite3
import hashlib

FORENSIC_DB = os.path.expanduser("~/CivicAdvocate.OS/forensic_ledger.db")

def verify_master_seals() -> bool:
    if not os.path.exists(FORENSIC_DB):
        print(f"[!] Database file '{FORENSIC_DB}' not found.")
        sys.exit(1)

    audit_passed = True

    with sqlite3.connect(FORENSIC_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT seal_id, timestamp, payout_digest_sha256, payload_hash_sha512, master_seal_hash FROM master_seals;"
        )
        rows = cursor.fetchall()

        if not rows:
            print("[!] No seal records found in master_seals table.")
            return False

        print(f"[*] Auditing {len(rows)} master seal record(s) in '{FORENSIC_DB}'...\n")

        for seal_id, ts, payout_digest, payload_hash, stored_master_seal in rows:
            # Recompute seed: payload_hash_sha512 + ":" + payout_digest_sha256
            combined_seed = f"{payload_hash}:{payout_digest}".encode("utf-8")
            computed_master_seal = hashlib.sha512(combined_seed).hexdigest()

            if computed_master_seal == stored_master_seal:
                print(f"  [PASS] Seal ID #{seal_id} ({ts})")
                print(f"         Stored Digest:   {stored_master_seal[:32]}...")
                print(f"         Computed Digest: {computed_master_seal[:32]}...")
            else:
                print(f"  [FAIL] Seal ID #{seal_id} HASH MISMATCH DETECTED!")
                print(f"         Stored:   {stored_master_seal}")
                print(f"         Computed: {computed_master_seal}")
                audit_passed = False

    print("\n=========================================")
    if audit_passed:
        print("[+] FORENSIC AUDIT PASSED: All master seal SHA-512 digests match canonical seeds.")
    else:
        print("[!] FORENSIC AUDIT FAILED: Cryptographic hash mismatch detected in ledger.")
    print("=========================================")
    return audit_passed

if __name__ == "__main__":
    success = verify_master_seals()
    sys.exit(0 if success else 1)
