import json

with open("dfr_compliance_audit.json") as f:
    data = json.load(f)

audit_findings = []

for item in data:
    reg_id = item.get("RegistryId")
    name = item.get("FacilityName")
    city = item.get("City")
    dfr = item.get("DFR_Data", {})
    
    permits = dfr.get("Permits", []) if isinstance(dfr.get("Permits"), list) else []
    formal_actions = dfr.get("FormalActions", []) if isinstance(dfr.get("FormalActions"), list) else []
    violations = dfr.get("ViolationsEnforcementActions", []) if isinstance(dfr.get("ViolationsEnforcementActions"), list) else []
    comp_summary = dfr.get("ComplianceSummary", {}) if isinstance(dfr.get("ComplianceSummary"), dict) else {}
    
    permit_systems = sorted(list(set([p.get("System") for p in permits if isinstance(p, dict) and p.get("System")])))
    
    record = {
        "RegistryId": reg_id,
        "FacilityName": name,
        "City": city,
        "PermitCount": len(permits),
        "PermitSystems": permit_systems,
        "FormalActionsCount": len(formal_actions),
        "ViolationsCount": len(violations),
        "ComplianceStatus": comp_summary.get("HasComplianceTracking", "N/A")
    }
    audit_findings.append(record)

flagged = [f for f in audit_findings if f["PermitCount"] > 0 or f["FormalActionsCount"] > 0 or f["ViolationsCount"] > 0]

print(f"[*] Audit Complete Across {len(audit_findings)} Target Sites:")
print(f"    - Facilities with Permitted Programs / Compliance Data: {len(flagged)}")
print(f"    - Total Facilities Audited: {len(audit_findings)}\n")

with open("forensic_compliance_summary.json", "w") as out:
    json.dump(audit_findings, out, indent=2)

print("[+] Forensic compliance summary generated -> forensic_compliance_summary.json")
