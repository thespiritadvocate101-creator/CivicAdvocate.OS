import json
import urllib.request
import urllib.error
import time

with open("filtered_high_priority_facilities.json") as f:
    facilities = json.load(f)

print(f"[*] Initiating program-specific CWA & RCRA compliance audit across {len(facilities)} target facilities...")

audit_results = []

for idx, fac in enumerate(facilities):
    reg_id = fac.get("RegistryId")
    name = fac.get("FacilityName")
    city = fac.get("CityName", "N/A")
    
    print(f"[{idx+1}/{len(facilities)}] Querying Registry ID: {reg_id} - {name}...")
    
    endpoints = {
        "CWA": f"https://ofmpub.epa.gov/apex/echo/cwa_rest_services.get_facility_info?p_id={reg_id}&output=JSON",
        "RCRA": f"https://ofmpub.epa.gov/apex/echo/rcra_rest_services.get_facility_info?p_id={reg_id}&output=JSON"
    }
    
    fac_data = {
        "RegistryId": reg_id,
        "FacilityName": name,
        "City": city,
        "CWA_Data": {},
        "RCRA_Data": {}
    }
    
    for prog, url in endpoints.items():
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'CivicAdvocate.OS-Auditor/2.0 (Architect@CivicAdvocate)'}
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    payload = json.loads(response.read().decode('utf-8'))
                    if prog == "CWA":
                        fac_data["CWA_Data"] = payload
                    else:
                        fac_data["RCRA_Data"] = payload
                    break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(2 * (attempt + 1))
                else:
                    break
            except Exception:
                break
            time.sleep(0.3)
            
    audit_results.append(fac_data)

with open("program_compliance_audit.json", "w") as out:
    json.dump(audit_results, out, indent=2)

print(f"[+] SUCCESS: Compiled program-specific records for {len(audit_results)} facilities into program_compliance_audit.json")
