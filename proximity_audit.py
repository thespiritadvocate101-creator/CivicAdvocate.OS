import json
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance in miles between two points."""
    R = 3958.8 # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def run_proximity_audit():
    # Load GeoJSON boundary polygon vertices
    with open("abstract_544_boundary.geojson", "r") as f:
        geo_data = json.load(f)
    polygon_ring = geo_data["features"][0]["geometry"]["coordinates"][0]

    # Load EPA facilities
    with open("epa_facilities_audit.json", "r") as f:
        epa_data = json.load(f)

    facilities = epa_data.get("Results", {}).get("FRSFacility", [])
    buffer_miles = 0.5  # 0.5 mile proximity threshold
    nearby_facilities = []

    for fac in facilities:
        try:
            lat = float(fac.get("Latitude83", 0))
            lon = float(fac.get("Longitude83", 0))
            if lat == 0.0 or lon == 0.0:
                continue
            
            # Check distance to any vertex or polygon centroid
            # For simplicity, check distance to polygon vertices
            min_dist = min(haversine_distance(lat, lon, pt[1], pt[0]) for pt in polygon_ring)
            
            if min_dist <= buffer_miles:
                fac["proximity_miles"] = round(min_dist, 3)
                nearby_facilities.append(fac)
        except (ValueError, TypeError):
            continue

    # Sort by proximity
    nearby_facilities.sort(key=lambda x: x["proximity_miles"])

    print(f"[*] Total Facilities Scanned: {len(facilities)}")
    print(f"[+] Facilities within {buffer_miles} miles of Abstract 544: {len(nearby_facilities)}\n")

    for fac in nearby_facilities[:15]:
        print(f"  - Facility Name : {fac.get('FacilityName')}")
        print(f"    Registry ID   : {fac.get('RegistryId')}")
        print(f"    Distance      : {fac.get('proximity_miles')} miles")
        print(f"    Location      : {fac.get('LocationAddress')}, {fac.get('CityName')}")
        print("-" * 50)

    output = {
        "target_abstract": "Abstract 544",
        "buffer_radius_miles": buffer_miles,
        "nearby_count": len(nearby_facilities),
        "facilities": nearby_facilities
    }
    with open("nearby_facilities_buffer.json", "w") as out:
        json.dump(output, out, indent=2)
    print("\n[+] Proximity audit results persisted to nearby_facilities_buffer.json")

if __name__ == "__main__":
    run_proximity_audit()
