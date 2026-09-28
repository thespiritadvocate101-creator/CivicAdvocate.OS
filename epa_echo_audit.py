import urllib.request
import json

def query_epa_facilities():
    lat = 32.4200
    lon = -97.3800
    radius = 5.0  # miles
    
    url = f"https://ofmpub.epa.gov/frs_public2/frs_rest_services.get_facilities?latitude83={lat}&longitude83={lon}&search_radius={radius}&output=JSON"
    
    print(f"[*] Querying EPA FRS REST API for facilities within {radius} miles of Abstract 544 ({lat}, {lon})...")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CivicAdvocate.OS-Auditor/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            facilities = data.get('Results', {}).get('FRSFacility', [])
            print(f"\n[+] Total Regulated Facilities Found: {len(facilities)}\n")
            
            for fac in facilities[:10]:  # Display top 10 results
                print(f"  - Facility Name : {fac.get('FacilityName')}")
                print(f"    Registry ID   : {fac.get('RegistryId')}")
                print(f"    Address       : {fac.get('LocationAddress')}, {fac.get('CityName')}, {fac.get('StateAbbr')} {fac.get('ZipCode')}")
                print(f"    County        : {fac.get('CountyName')}")
                print("-" * 50)
                
            # Save raw results for offline inspection
            with open("epa_facilities_audit.json", "w") as out:
                json.dump(data, out, indent=2)
            print("\n[+] Full EPA audit payload saved to epa_facilities_audit.json")
            
    except Exception as e:
        print(f"[-] Failed to query EPA REST API: {e}")

if __name__ == "__main__":
    query_epa_facilities()
