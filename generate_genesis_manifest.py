#!/usr/bin/env python3
import json
import hashlib
import os
import sys

covenant_file = "sovereign_covenant.md"

# Verify and compute live SHA-512 of sovereign_covenant.md
if os.path.exists(covenant_file):
    with open(covenant_file, "rb") as f:
        covenant_sha512 = hashlib.sha512(f.read()).hexdigest()
else:
    covenant_sha512 = "9890d4e699dbc80308b8c81ce2bdcaeba5d24fab60bbc7572dacebe2be5a237f75e705af0f8311ae45d073370b383cc196d0eb069095acfa6cde60cc7bca5c04"

manifest = {
    "manifest_version": "1.0.0",
    "system": "CivicAdvocate.OS",
    "timestamp_iso": "2026-09-27T11:15:00-05:00",
    "signatory": {
        "legal_name": "Brandon Lynn Campbell",
        "moniker": "#THE~SPIRIT~ADVOCATE",
        "jurisdiction": "Marystown, Johnson County, Texas",
        "survey": "Abstract 544 (Silas Elbert Bandy Survey)"
    },
    "cryptographic_anchors": {
        "covenant_sha512": covenant_sha512,
        "arbitrum_tx_signature": "60b65544d6903ebe2539b11dfe4202645982fd8ba6fbcfdcd95b32d4cae3b6d5",
        "ipfs_canonical_cid": "QmQCQY81UQsBLudNYPBwdyPzksHRMqV48cPaRy49ARu5mx"
    },
    "network_infrastructure": {
        "p2p_protocol": "Kubo IPFS",
        "peer_id": "12D3KooWLruVgp8TprcCeRiPM1XdhjoSQqZ9xYJ53i8sjZk3r8gA",
        "rpc_api": "/ip4/127.0.0.1/tcp/5001",
        "gateway": "/ip4/127.0.0.1/tcp/8081",
        "mdns_enabled": False,
        "telemetry_enabled": False
    },
    "repository_state": {
        "git_commit": "08e605d94bb5465c4e56db2ad7b92b8fc40bf37a",
        "branch": "main",
        "commit_subject": "SYS_LOCK: Sovereign Covenant Genesis State"
    }
}

with open("genesis_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=4)

print("===================================================")
print("[+] genesis_manifest.json created successfully.")
print(f"[+] SHA-512 Hash: {covenant_sha512}")
print("===================================================")
