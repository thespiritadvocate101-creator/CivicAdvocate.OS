import json

with open("dfr_compliance_audit.json") as f:
    data = json.load(f)

print("=== DEEP QUARTERLY COMPLIANCE & PROGRAM MATRIX AUDIT ===")

program_breakdown = {}
snc_hpv_flags = []

for item in data:
    reg_id = item.get("RegistryId")
    name = item.get("FacilityName")
    city = item.get("City")
    dfr = item.get("DFR_Data", {})
    
    permits = dfr.get("Permits", []) if isinstance(dfr.get("Permits"), list) else []
    systems = set()
    for p in permits:
        if isinstance(p, dict) and p.get("System"):
            sys_name = p.get("System")
            systems.add(sys_name)
            program_breakdown[sys_name] = program_breakdown.get(sys_name, 0) + 1
            
    dfr_str = json.dumps(dfr).lower()
    has_snc = "significant non-compliance" in dfr_str or '"snc"' in dfr_str
    has_hpv = "high priority violation" in dfr_str or '"hpv"' in dfr_str
    
    if has_snc or has_hpv:
        snc_hpv_flags.append({
            "RegistryId": reg_id,
            "FacilityName": name,
            "City": city,
            "Systems": list(systems),
            "SNC": has_snc,
            "HPV": has_hpv
        })

print(f"\n[+] Active Permit System Distribution across Abstract 544 Target Area:")
for sys_name, count in sorted(program_breakdown.items(), key=lambda x: x[1], reverse=True):
    print(f"    - {sys_name}: {count} permitted records")

print(f"\n[+] Significant Non-Compliance / High-Priority Violation Flags: {len(snc_hpv_flags)}")
for flag in snc_hpv_flags:
    print(f"    - [{flag['RegistryId']}] {flag['FacilityName']} ({flag['City']}) | Systems: {flag['Systems']}")

