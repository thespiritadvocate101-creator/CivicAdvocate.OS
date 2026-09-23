import os
import sys
import json
import sqlite3
import hashlib
from datetime import datetime

PAYOUTS_DB = os.path.expanduser("~/payouts.db")
FORENSIC_DB = os.path.expanduser("~/CivicAdvocate.OS/forensic_ledger.db")


def get_latest_payout_digest(db_path: str = PAYOUTS_DB) -> str:
    """Retrieves the most recent digest_sha256 from payouts.db."""
    if not os.path.exists(db_path):
        return "0" * 64

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT digest_sha256 FROM payout_batches ORDER BY rowid DESC LIMIT 1;"
            )
            row = cursor.fetchone()
            return row[0] if row and row[0] else "0" * 64
    except Exception as e:
        print(f"[!] Warning: Unable to read payouts.db digest: {e}")
        return "0" * 64


def ensure_forensic_schema(conn: sqlite3.Connection):
    """Ensures the master forensic seal table contains the payout_digest column."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS master_seals (
            seal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            payout_digest_sha256 TEXT NOT NULL,
            payload_hash_sha512 TEXT NOT NULL,
            master_seal_hash TEXT NOT NULL
        );
    """
    )
    conn.commit()


def commit_master_ledger():
    payout_digest = get_latest_payout_digest()
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Construct unified payload state
    payload_data = {
        "timestamp": timestamp,
        "payout_digest_sha256": payout_digest,
        "system_tag": "CivicAdvocate.OS",
    }

    canonical_payload = json.dumps(
        payload_data, sort_keys=True, separators=(",", ":")
    )
    payload_hash = hashlib.sha512(
        canonical_payload.encode("utf-8")
    ).hexdigest()

    # Compute combined master seal digest
    combined_seed = f"{payload_hash}:{payout_digest}".encode("utf-8")
    master_seal_hash = hashlib.sha512(combined_seed).hexdigest()

    with sqlite3.connect(FORENSIC_DB) as conn:
        ensure_forensic_schema(conn)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO master_seals (timestamp, payout_digest_sha256, payload_hash_sha512, master_seal_hash)
            VALUES (?, ?, ?, ?);
        """,
            (timestamp, payout_digest, payload_hash, master_seal_hash),
        )
        conn.commit()

    print(f"[✓] MASTER LEDGER SEALED")
    print(f"    Payout SHA-256: {payout_digest}")
    print(f"    Master Seal:    {master_seal_hash[:32]}...")


if __name__ == "__main__":
    commit_master_ledger()
