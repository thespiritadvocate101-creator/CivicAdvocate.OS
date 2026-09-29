import json

with open("forensic_compliance_summary.json") as f:
    records = json.load(f)

enforcement_sites = [r for r in records if r["FormalActionsCount"] > 0 or r["ViolationsCount"] > 0]
multi_permit_sites = [r for r in records if r["PermitCount"] > 1]

print("=== ABSTRACT 544 COMPLIANCE LEDGER SUMMARY ===")
print(f"Total Facilities Audited: {len(records)}")
print(f"Multi-Permit Facilities: {len(multi_permit_sites)}")
print(f"Sites with Violations / Formal Actions: {len(enforcement_sites)}\n")

if enforcement_sites:
    print("--- HIGH-RISK / ACTION FLAGGED SITES ---")
    for r in enforcement_sites:
        reg_id = r['RegistryId']
        fac_name = r['FacilityName']
        city = r['City']
        permits = r['PermitCount']
        systems = r['PermitSystems']
        violations = r['ViolationsCount']
        actions = r['FormalActionsCount']
        print(f"[{reg_id}] {fac_name} ({city})")
        print(f"  Permits: {permits} {systems}")
        print(f"  Violations: {violations} | Formal Actions: {actions}\n")
else:
    print("[+] No formal enforcement actions or active violations recorded in top-level counters.")
