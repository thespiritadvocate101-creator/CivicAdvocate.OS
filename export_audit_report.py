import os
import sys
import json
import sqlite3
import hashlib
from datetime import datetime

PAYOUTS_DB = os.path.expanduser("~/payouts.db")
FORENSIC_DB = os.path.expanduser("~/CivicAdvocate.OS/forensic_ledger.db")
OUTPUT_DIR = os.path.expanduser("~/CivicAdvocate.OS/audit_reports")


def fetch_payouts_data():
    payouts = []
    if not os.path.exists(PAYOUTS_DB):
        return payouts

    with sqlite3.connect(PAYOUTS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT payout_batch_id, batch_status, time_created, time_completed, digest_sha256 FROM payout_batches;"
        )
        for row in cursor.fetchall():
            batch_id = row[0]
            batch_entry = {
                "payout_batch_id": batch_id,
                "batch_status": row[1],
                "time_created": row[2],
                "time_completed": row[3],
                "digest_sha256": row[4],
                "items": [],
            }

            # Retrieve associated items
            try:
                item_cursor = conn.cursor()
                item_cursor.execute(
                    "SELECT payout_item_id, transaction_status, digest_sha256 FROM payout_items WHERE payout_batch_id = ?;",
                    (batch_id,),
                )
                for item_row in item_cursor.fetchall():
                    batch_entry["items"].append(
                        {
                            "payout_item_id": item_row[0],
                            "transaction_status": item_row[1],
                            "digest_sha256": item_row[2],
                        }
                    )
            except sqlite3.OperationalError:
                pass

            payouts.append(batch_entry)
    return payouts


def fetch_master_seals():
    seals = []
    if not os.path.exists(FORENSIC_DB):
        return seals

    with sqlite3.connect(FORENSIC_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT seal_id, timestamp, payout_digest_sha256, payload_hash_sha512, master_seal_hash FROM master_seals;"
        )
        for row in cursor.fetchall():
            seals.append(
                {
                    "seal_id": row[0],
                    "timestamp": row[1],
                    "payout_digest_sha256": row[2],
                    "payload_hash_sha512": row[3],
                    "master_seal_hash": row[4],
                }
            )
    return seals


def generate_audit_report():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts_now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_filename = f"audit_report_{ts_now}.json"
    report_path = os.path.join(OUTPUT_DIR, report_filename)

    payout_records = fetch_payouts_data()
    seal_records = fetch_master_seals()

    report_payload = {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "framework": "CivicAdvocate.OS",
            "total_payout_batches": len(payout_records),
            "total_master_seals": len(seal_records),
        },
        "payout_records": payout_records,
        "master_seals": seal_records,
    }

    # Canonicalize and sign report content
    canonical_bytes = json.dumps(
        report_payload, sort_keys=True, indent=2
    ).encode("utf-8")
    report_sha512 = hashlib.sha512(canonical_bytes).hexdigest()

    # Embed digest into wrapper
    final_report = {
        "report_sha512": report_sha512,
        "report": report_payload,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)

    print(f"[✓] FORENSIC REPORT GENERATED")
    print(f"    File:          {report_path}")
    print(f"    Report SHA512: {report_sha512[:32]}...")
    print(
        f"    Records:       {len(payout_records)} Payouts | {len(seal_records)} Master Seals"
    )


if __name__ == "__main__":
    generate_audit_report()
