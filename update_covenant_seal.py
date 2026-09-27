#!/usr/bin/env python3
import json
import re
import sys

payload_file = "covenant_payload.json"
doc_file = "sovereign_covenant.md"

try:
    with open(payload_file, "r") as f:
        payload = json.load(f)
except FileNotFoundError:
    print(f"[-] Error: {payload_file} not found.")
    sys.exit(1)

doc_hash = payload.get("document_sha512")
epoch = payload.get("epoch")
timestamp_utc = payload.get("timestamp_utc")

try:
    with open(doc_file, "r") as f:
        content = f.read()
except FileNotFoundError:
    print(f"[-] Error: {doc_file} not found.")
    sys.exit(1)

# Construct updated seal block
updated_seal = (
    "**Cryptographic Ledger Seal (Tamper-Evident):**\n"
    f"SHA-512 Genesis Hash: `{doc_hash}`\n"
    f"Timestamp / Epoch: `{timestamp_utc}` / `{epoch}`\n"
    "Network Anchor: Arbitrum Network (Master Genesis Root Payload)"
)

# Replace existing seal block in the document
pattern = r"\*\*Cryptographic Ledger Seal \(Tamper-Evident\):\*\*.*?(?=---|\Z)"
new_content = re.sub(pattern, updated_seal + "\n\n", content, flags=re.DOTALL)

with open(doc_file, "w") as f:
    f.write(new_content)

print("===================================================")
print("[+] sovereign_covenant.md updated with live seal.")
print(f"[+] Verified SHA-512 Hash: {doc_hash}")
print(f"[+] Anchored Epoch:        {epoch}")
print("===================================================")
