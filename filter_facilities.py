import json

with open("epa_facilities_audit.json") as f:
    data = json.load(f)

facs = data.get("Results", {}).get("FRSFacility", [])

# Keywords of interest for forensic cadastral auditing
keywords = ["OIL", "GAS", "PIPELINE", "WATER", "DISPOSAL", "ENERGY", "SWD", "CORP", "INC"]

print(f"[*] Scanning {len(facs)} facilities for high-priority keywords...")
filtered = []
for x in facs:
    name = x.get("FacilityName", "").upper()
    if any(kw in name for kw in keywords):
        filtered.append(x)

print(f"[+] Found {len(filtered)} matching facilities:")
for f in filtered[:15]:  # Display top 15 matches
    print(f"  - [{f.get('RegistryId')}] {f.get('FacilityName')} ({f.get('CityName', 'N/A')})")

with open("filtered_high_priority_facilities.json", "w") as out:
    json.dump(filtered, out, indent=2)
print("[+] Filtered records successfully saved to filtered_high_priority_facilities.json")
