#!/usr/bin/env bash

INPUT_FILE="nearby_facilities_buffer.json"
OUTPUT_MD="abstract_544_proximity_ledger.md"

if [ ! -f "$INPUT_FILE" ]; then
    echo "[-] Error: $INPUT_FILE not found in current directory."
    exit 1
fi

# Generate Python 3.12+ compliant UTC timestamp using standard coreutils
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Initialize the Markdown file using a heredoc block
cat <<EOF > "$OUTPUT_MD"
# CivicAdvocate.OS Proximity Ledger
**Target:** Silas Elbert Bandy Survey (Abstract 544) | Johnson County, TX
**Audit Timestamp (UTC):** $TIMESTAMP
---

## EPA Facility Records

EOF

# Parse JSON dynamically with jq, extracting fields regardless of casing or array/object structure
jq -r '
  if type == "object" then .[] else .[]? // . end |
  select(type == "object") |
  "### \(.name // .["Facility Name"] // .facility_name // "UNKNOWN")\n- **Registry ID:** \`\(.registry_id // .["Registry ID"] // "N/A")\`\n- **Distance:** \(.distance // .["Distance"] // "N/A")\n- **Location:** \(.location // .["Location"] // "N/A")\n"
' "$INPUT_FILE" >> "$OUTPUT_MD"

# Generate SHA-256 hash of the final payload content
PAYLOAD_HASH=$(sha256sum "$OUTPUT_MD" | awk '{print $1}')

# Append the cryptographic signature block
cat <<EOF >> "$OUTPUT_MD"
---
**Payload SHA-256 Signature:** \`$PAYLOAD_HASH\`
EOF

echo "[+] Ledger successfully compiled to $OUTPUT_MD"
echo "[*] Payload SHA-256 Signature: $PAYLOAD_HASH"
