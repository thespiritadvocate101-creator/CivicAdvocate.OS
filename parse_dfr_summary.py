import json

with open("dfr_compliance_audit.json") as f:
    data = json.load(f)

print(f"[*] Parsing DFR compliance payload across {len(data)} target facilities...\n")

summary = []
for item in data:
    reg_id = item.get("RegistryId")
    name = item.get("FacilityName")
    city = item.get("City")
    dfr = item.get("DFR_Data", {})
    
    # Extract top-level DFR section keys if present
    dfr_keys = list(dfr.keys()) if isinstance(dfr, dict) else []
    
    summary.append({
        "RegistryId": reg_id,
        "FacilityName": name,
        "City": city,
        "DFR_Keys": dfr_keys
    })

print(f"[+] Successfully extracted structural keys for {len(summary)} facility records.")
if summary:
    print(f"[*] Top-level DFR section keys present in payload (Facility 1): {summary[0]['DFR_Keys']}\n")

with open("dfr_parsed_summary.json", "w") as out:
    json.dump(summary, out, indent=2)

print("[+] Structural extraction complete. Saved to dfr_parsed_summary.json")
