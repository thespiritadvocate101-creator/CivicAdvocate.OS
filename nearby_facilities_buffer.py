import json
import hashlib
from datetime import datetime

def generate_proximity_ledger():
    input_file = 'nearby_facilities_buffer.json'
    output_md = 'abstract_544_proximity_ledger.md'
    
    try:
        with open(input_file, 'r') as f:
            facilities = json.load(f)
    except FileNotFoundError:
        print("[-] Error: nearby_facilities_buffer.json not found in current directory.")
        return

    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Constructing the Markdown payload
    md_content = f"# CivicAdvocate.OS Proximity Ledger\n"
    md_content += f"**Target:** Silas Elbert Bandy Survey (Abstract 544) | Johnson County, TX\n"
    md_content += f"**Audit Timestamp (UTC):** {timestamp}\n"
    md_content += f"**Total Facilities within Buffer:** {len(facilities)}\n\n"
    md_content += "---\n\n"
    md_content += "## EPA Facility Records\n\n"

    for fac in facilities:
        # Assuming the JSON contains 'name', 'registry_id', 'distance', 'location'
        name = fac.get('name', 'UNKNOWN')
        reg_id = fac.get('registry_id', 'N/A')
        distance = fac.get('distance', 'N/A')
        location = fac.get('location', 'N/A')
        
        md_content += f"### {name}\n"
        md_content += f"- **Registry ID:** `{reg_id}`\n"
        md_content += f"- **Distance:** {distance} miles\n"
        md_content += f"- **Location:** {location}\n\n"

    # Generate a SHA-256 hash of the payload content
    payload_hash = hashlib.sha256(md_content.encode('utf-8')).hexdigest()
    md_content += "---\n"
    md_content += f"**Payload SHA-256 Signature:** `{payload_hash}`\n"

    with open(output_md, 'w') as f:
        f.write(md_content)

    print(f"[+] Ledger successfully compiled to {output_md}")
    print(f"[*] Payload SHA-256 Signature: {payload_hash}")
    print(f"[*] System ready for PDF rendering or payload packaging.")

if __name__ == '__main__':
    generate_proximity_ledger()
