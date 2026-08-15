#!/usr/bin/env python3
import sqlite3
import hashlib
import json
from datetime import datetime, timezone

DB_NAME = "audit_ledger.db"
OUTPUT_FILE = "audit_report_latest.md"

def generate_markdown_report():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query latest written root
    cursor.execute("SELECT * FROM audit_records ORDER BY id DESC LIMIT 1;")
    genesis_row = cursor.fetchone()

    if not genesis_row:
        print("[!] No audit records found in audit_ledger.db.")
        return

    # Gather table counts
    tables = [
        ("normalized_federal_awards", "Federal Awards"),
        ("normalized_state_expenditures", "State Expenditures"),
        ("normalized_local_rrc", "Local RRC Records"),
        ("cross_reference_matches", "Cross-Reference Matches"),
        ("audit_records", "Audit Ledger Roots")
    ]
    counts = {}
    for tbl, label in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        counts[label] = cursor.fetchone()[0]

    # Fetch active cross-reference matches
    cursor.execute("SELECT federal_entity, state_entity, similarity_score, match_type FROM cross_reference_matches ORDER BY similarity_score DESC;")
    matches = cursor.fetchall()

    # Build Markdown document
    md = []
    md.append("# CivicAdvocate.OS Audit Ledger Report")
    md.append(f"**Report Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    md.append(f"**Genesis Record ID:** #{genesis_row['id']}")
    md.append(f"**Ledger Layer:** {genesis_row['layer']}")
    md.append(f"**Record Timestamp:** {genesis_row['timestamp']}")
    md.append("")

    md.append("## Ledger Record Summary")
    md.append("| Table / Layer | Total Indexed Records |")
    md.append("| :--- | :--- |")
    for label, count in counts.items():
        md.append(f"| {label} | {count} |")
    md.append("")

    md.append("## Cryptographic Genesis Root")
    md.append(f"- **Source Authority:** `{genesis_row['source']}`")
    md.append(f"- **State SHA-512 Root:** `{genesis_row['payload_sha512']}`")
    md.append("")

    if genesis_row['raw_data']:
        try:
            raw_json = json.loads(genesis_row['raw_data'])
            md.append("### Manifest Payload")
            md.append("```json")
            md.append(json.dumps(raw_json, indent=2))
            md.append("```")
            md.append("")
        except Exception:
            pass

    md.append("## Entity Cross-Reference Matches")
    if matches:
        md.append("| Federal Entity | State Entity | Similarity Score | Match Type |")
        md.append("| :--- | :--- | :--- | :--- |")
        for m in matches:
            md.append(f"| {m['federal_entity']} | {m['state_entity']} | {m['similarity_score']:.2f} | {m['match_type']} |")
    else:
        md.append("*No entity overlaps found matching or exceeding the similarity threshold.*")
    md.append("")

    document_body = "\n".join(md)

    # Generate document body SHA-512 signature seal
    body_signature = hashlib.sha512(document_body.encode('utf-8')).hexdigest()

    # Append Attestation Seal Footer
    footer = []
    footer.append("---")
    footer.append("## Cryptographic Attestation & Signature")
    footer.append("This report was automatically compiled and verified from `audit_ledger.db`.")
    footer.append(f"- **Report Body SHA-512 Signature:** `{body_signature}`")
    footer.append(f"- **State SHA-512 Genesis Anchor:** `{genesis_row['payload_sha512']}`")
    footer.append("")

    full_document = document_body + "\n" + "\n".join(footer)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_document)

    conn.close()
    print(f"[+] Signed Markdown report written to {OUTPUT_FILE}")
    print(f"[+] Report Signature: {body_signature[:32]}...")

if __name__ == "__main__":
    generate_markdown_report()
