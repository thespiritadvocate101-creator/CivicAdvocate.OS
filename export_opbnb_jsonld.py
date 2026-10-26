import psycopg2
import json
from datetime import datetime, timezone

# Connect to the local PostgreSQL socket
conn = psycopg2.connect(dbname="civic_audit", host="/data/data/com.termux/files/usr/tmp")
cur = conn.cursor()

# Fetch all cryptographically sealed records
cur.execute("""
    SELECT tx_hash, block_num, from_address, to_address, asset, value_wei, sha512_seal, inserted_at 
    FROM opbnb_transfers 
    WHERE sha512_seal IS NOT NULL 
    ORDER BY block_num ASC;
""")
records = cur.fetchall()

# Construct the W3C JSON-LD Verifiable Credential wrapper
json_ld_document = {
    "@context": [
        "https://www.w3.org/2018/credentials/v1",
        "https://w3id.org/security/suites/ed25519-2020/v1"
    ],
    "id": f"urn:uuid:civicadvocate-audit-opbnb-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
    "type": ["VerifiableCredential", "AuditLedger"],
    "issuer": "urn:did:civicadvocate:os:core",
    "issuanceDate": datetime.now(timezone.utc).isoformat() + "Z",
    "credentialSubject": {
        "id": "urn:civicadvocate:opbnb:transfers",
        "transfers": []
    }
}

# Populate the credential subject with the sealed transfer nodes
for r in records:
    transfer_node = {
        "type": "BlockchainTransfer",
        "txHash": r[0],
        "blockNumber": r[1],
        "from": r[2],
        "to": r[3],
        "asset": r[4],
        "valueWei": str(r[5]),
        "evidenceSeal": r[6],
        "recordedAt": r[7].isoformat() if r[7] else None
    }
    json_ld_document["credentialSubject"]["transfers"].append(transfer_node)

# Write out the JSON-LD artifact
output_path = "/data/data/com.termux/files/home/CivicAdvocate.OS/opbnb_ledger.jsonld"
with open(output_path, "w") as f:
    json.dump(json_ld_document, f, indent=2)

print(f"Successfully exported {len(records)} sealed records to {output_path}")

cur.close()
conn.close()
