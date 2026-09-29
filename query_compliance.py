import json
import urllib.request
import urllib.error
import time

with open("filtered_high_priority_facilities.json") as f:
    facilities = json.load(f)

print(f"[*] Initiating dual NPDES & RCRA compliance audit across {len(facilities)} target facilities...")

audit_results = []

for idx, fac in enumerate(facilities):
    reg_id = fac.get("RegistryId")
    name = fac.get("FacilityName")
    city = fac.get("CityName")
    
    # ECHO REST service endpoint for facility compliance summary
    url = f"https://ofmpub.epa.gov/apex/echo/rest_services/get_facility_info?p_id={reg_id}&output=JSON"
    
    print(f"[{idx+1}/{len(facilities)}] Querying Registry ID: {reg_id} - {name}...")
    
    success = False
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'CivicAdvocate.OS-Auditor/1.0 (Architect@CivicAdvocate)'}
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode('utf-8'))
                audit_results.append({
                    "RegistryId": reg_id,
                    "FacilityName": name,
                    "City": city,
                    "ComplianceData": payload
                })
                success = True
                break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 * (attempt + 1))
            else:
                break
        except Exception:
            break
            
        time.sleep(0.3)

with open("compliance_audit_results.json", "w") as out:
    json.dump(audit_results, out, indent=2)

print(f"[+] SUCCESS: Compiled compliance records for {len(audit_results)} facilities into compliance_audit_results.json")
