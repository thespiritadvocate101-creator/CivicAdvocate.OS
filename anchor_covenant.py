#!/usr/bin/env python3
import json
import time
import hashlib
from datetime import datetime, timezone

# Covenant Parameters
DOCUMENT_HASH = "9890d4e699dbc80308b8c81ce2bdcaeba5d24fab60bbc7572dacebe2be5a237f75e705af0f8311ae45d073370b383cc196d0eb069095acfa6cde60cc7bca5c04"
ARCHITECT = "Brandon Lynn Campbell | #THE~SPIRIT~ADVOCATE"
SPATIAL_ANCHOR = "Abstract 544 (Silas Elbert Bandy Survey), Marystown, Johnson County, Texas"
NETWORK_TARGET = "Arbitrum"

def compile_genesis_payload():
    current_epoch = int(time.time())
    iso_timestamp = datetime.fromtimestamp(current_epoch, tz=timezone.utc).isoformat()
    
    payload = {
        "architect": ARCHITECT,
        "spatial_anchor": SPATIAL_ANCHOR,
        "document_sha512": DOCUMENT_HASH,
        "network_target": NETWORK_TARGET,
        "epoch": current_epoch,
        "timestamp_utc": iso_timestamp,
        "protocol": "IMMUTABLE_TRUTH_ANCHOR"
    }
    
    # Serialize deterministically for cryptographic signing
    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    
    # Generate the transaction hash for the payload
    tx_signature = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()
    
    print("===================================================")
    print("       MASTER GENESIS ROOT PAYLOAD COMPILED        ")
    print("===================================================")
    print(f"[+] Document Hash: {DOCUMENT_HASH}")
    print(f"[+] TX Signature:  {tx_signature}")
    print(f"[+] Epoch Anchor:  {current_epoch}")
    print("===================================================")
    print("Writing payload to covenant_payload.json...")
    
    with open("covenant_payload.json", "w") as f:
        f.write(payload_json)
        
    print("Payload ready for decentralized broadcast.")

if __name__ == "__main__":
    compile_genesis_payload()
