#!/usr/bin/env bash
set -euo pipefail

echo "[+] Starting integrity verification for CivicAdvocate.OS ledger files..."

if [ -f "audit_summary.json" ]; then
  echo "[*] Checking audit_summary.json for masterStateRoot..."
  python3 - <<'PY'
import json, sys
path = "audit_summary.json"
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as exc:
    print(f"[FAIL] Unable to parse {path}: {exc}", file=sys.stderr)
    raise SystemExit(1)

if "masterStateRoot" not in data:
    print(f"[FAIL] {path} is missing the required masterStateRoot field.", file=sys.stderr)
    raise SystemExit(1)

value = str(data["masterStateRoot"]).strip()
if not value:
    print(f"[FAIL] {path} contains an empty masterStateRoot value.", file=sys.stderr)
    raise SystemExit(1)

print(f"[PASS] masterStateRoot present and non-empty: {value}")
PY
else
  echo "[WARN] audit_summary.json not found; skipping masterStateRoot validation."
fi

if [ -f "earmark_routing_manifest.json" ]; then
  echo "[*] Checking earmark_routing_manifest.json cryptographic seal..."
  python3 - <<'PY'
import json, hashlib, sys
path = "earmark_routing_manifest.json"

try:
    with open(path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
except Exception as exc:
    print(f"[FAIL] Unable to parse {path}: {exc}", file=sys.stderr)
    raise SystemExit(1)

stored = manifest.get("cryptographic_seal")
if stored is None:
    print(f"[FAIL] {path} is missing the cryptographic_seal field.", file=sys.stderr)
    raise SystemExit(1)

payload = {k: v for k, v in manifest.items() if k != "cryptographic_seal"}
canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
computed = hashlib.sha512(canonical.encode("utf-8")).hexdigest()

if stored != computed:
    print(f"[FAIL] Manifest seal mismatch. Stored={stored} Computed={computed}", file=sys.stderr)
    raise SystemExit(1)

print(f"[PASS] Manifest seal verified: {computed[:16]}...")
PY
else
  echo "[WARN] earmark_routing_manifest.json not found; skipping manifest seal validation."
fi

if [ -f "ledger_export.jsonld" ] && [ -f "ledger_export.jsonld.sha512" ]; then
  echo "[*] Verifying SHA-512 checksum..."
  sha512sum -c ledger_export.jsonld.sha512
else
  echo "[WARN] ledger_export.jsonld or checksum file not found; skipping SHA-512 validation."
fi

if [ -f "ledger_export.jsonld" ] && [ -f "ledger_export.jsonld.sig" ] && [ -f "ed25519_public.pem" ]; then
  echo "[*] Verifying Ed25519 signature..."
  openssl pkeyutl -verify -pubin -inkey ed25519_public.pem -sigfile ledger_export.jsonld.sig -in ledger_export.jsonld
  echo "[PASS] Ed25519 signature verification succeeded."
else
  echo "[WARN] Signature inputs not found; skipping Ed25519 validation."
fi

echo "[PASS] Ledger integrity verification completed successfully."
