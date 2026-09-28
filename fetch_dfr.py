import json
import urllib.request
import time

with open("filtered_high_priority_facilities.json") as f:
    facilities = json.load(f)

print(f"[*] Initiating DFR compliance audit via echodata.epa.gov across {len(facilities)} facilities...")

audit_results = []

for idx, fac in enumerate(facilities):
    reg_id = fac.get("RegistryId")
    name = fac.get("FacilityName")
    city = fac.get("CityName", "N/A")
    
    url = f"https://echodata.epa.gov/echo/dfr_rest_services.get_dfr?p_id={reg_id}&output=JSON"
    print(f"[{idx+1}/{len(facilities)}] Querying Registry ID: {reg_id} - {name}...")
    
    fac_entry = {
        "RegistryId": reg_id,
        "FacilityName": name,
        "City": city,
        "DFR_Data": {}
    }
    
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'CivicAdvocate.OS-Auditor/3.0 (Architect@CivicAdvocate)'}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                payload = json.loads(response.read().decode('utf-8'))
                fac_entry["DFR_Data"] = payload.get("Results", {})
                break
        except Exception as e:
            if attempt == 2:
                print(f"    [!] Failed to retrieve DFR for {reg_id}: {e}")
            time.sleep(1)
            
    audit_results.append(fac_entry)
    time.sleep(0.3)

with open("dfr_compliance_audit.json", "w") as out:
    json.dump(audit_results, out, indent=2)

print(f"[+] SUCCESS: Compiled DFR compliance records for {len(audit_results)} facilities into dfr_compliance_audit.json")
