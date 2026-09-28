import json

def point_in_polygon(x, y, poly):
    """Ray-casting algorithm to test if point (x, y) is inside polygon ring."""
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def run_spatial_filter():
    # Load GeoJSON boundary polygon
    with open("abstract_544_boundary.geojson", "r") as f:
        geo_data = json.load(f)
    
    polygon_ring = geo_data["features"][0]["geometry"]["coordinates"][0]

    # Load EPA facilities
    with open("epa_facilities_audit.json", "r") as f:
        epa_data = json.load(f)

    facilities = epa_data.get("Results", {}).get("FRSFacility", [])
    intersecting = []

    for fac in facilities:
        try:
            lat = float(fac.get("Latitude83", 0))
            lon = float(fac.get("Longitude83", 0))
            if lat == 0.0 or lon == 0.0:
                continue
            
            if point_in_polygon(lon, lat, polygon_ring):
                intersecting.append(fac)
        except (ValueError, TypeError):
            continue

    print(f"[*] Total Facilities Analyzed: {len(facilities)}")
    print(f"[+] Intersecting / Enclosed Facilities: {len(intersecting)}\n")

    for fac in intersecting:
        print(f"  - Facility Name : {fac.get('FacilityName')}")
        print(f"    Registry ID   : {fac.get('RegistryId')}")
        print(f"    Location      : {fac.get('LocationAddress')}, {fac.get('CityName')}")
        print(f"    Coordinates   : ({fac.get('Latitude83')}, {fac.get('Longitude83')})")
        print("-" * 50)

    output = {
        "target_abstract": "Abstract 544",
        "intersecting_count": len(intersecting),
        "facilities": intersecting
    }
    with open("intersecting_facilities.json", "w") as out:
        json.dump(output, out, indent=2)
    print("\n[+] Intersecting facilities persisted to intersecting_facilities.json")

if __name__ == "__main__":
    run_spatial_filter()
