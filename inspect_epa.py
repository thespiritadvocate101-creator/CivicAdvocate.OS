import json
from collections import Counter

def inspect_audit_file():
    try:
        with open("epa_facilities_audit.json", "r") as f:
            data = json.load(f)
        
        facilities = data.get('Results', {}).get('FRSFacility', [])
        print(f"[*] Total Facilities Loaded: {len(facilities)}")
        
        if not facilities:
            print("[-] No facility records found in payload.")
            return

        # Inspect available keys from the first record
        sample_keys = list(facilities[0].keys())
        print(f"\n[+] Available Facility Record Fields ({len(sample_keys)} total):")
        for key in sample_keys:
            print(f"    - {key}")

        # Aggregate by City
        cities = [fac.get('CityName', 'UNKNOWN') for fac in facilities]
        city_counts = Counter(cities)
        
        print("\n[+] Facility Distribution by City:")
        for city, count in city_counts.most_common(5):
            print(f"    - {city}: {count} facilities")

        # Display a detailed dump of the first facility record
        print("\n[+] Detailed Sample Record (Index 0):")
        print(json.dumps(facilities[0], indent=2))

    except Exception as e:
        print(f"[-] Error reading audit file: {e}")

if __name__ == "__main__":
    inspect_audit_file()
