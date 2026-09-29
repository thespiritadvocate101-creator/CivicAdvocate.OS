import json

with open("dfr_compliance_audit.json") as f:
    data = json.load(f)

# 1. Inspect first available permit object to verify key names
print("=== PERMIT DICTIONARY SCHEMA DIAGNOSTIC ===")
for item in data:
    dfr = item.get("DFR_Data", {})
    permits = dfr.get("Permits", []) if isinstance(dfr.get("Permits"), list) else []
    if permits and len(permits) > 0:
        first_permit = permits[0]
        if isinstance(first_permit, dict):
            print(f"[+] Sample Permit Keys ({item.get('FacilityName')}): {list(first_permit.keys())}")
            print(f"[+] Sample Permit Values: {first_permit}\n")
            break

# 2. Extract permit system counts dynamically across all facilities
system_counts = {}
statute_counts = {}

for item in data:
    dfr = item.get("DFR_Data", {})
    permits = dfr.get("Permits", []) if isinstance(dfr.get("Permits"), list) else []
    
    for p in permits:
        if isinstance(p, dict):
            sys_val = p.get("System") or p.get("SystemAcronym") or p.get("SourceSystem") or p.get("SystemType") or "Unknown"
            stat_val = p.get("Statute") or p.get("Program") or p.get("Code") or "Unknown"
            
            system_counts[sys_val] = system_counts.get(sys_val, 0) + 1
            statute_counts[stat_val] = statute_counts.get(stat_val, 0) + 1

print("=== PERMIT SYSTEM DISTRIBUTION ===")
for sys_name, count in sorted(system_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {sys_name}: {count} records")

print("\n=== REGULATORY STATUTE DISTRIBUTION ===")
for stat_name, count in sorted(statute_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {stat_name}: {count} records")

