import json
import math

# Abstract 544 reference centroid
CENTROID_LAT = 32.42
CENTROID_LON = -97.38

def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth radius in miles
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

with open("abstract_544_facilities.geojson") as f:
    geojson_data = json.load(f)

distance_ledger = []

for feature in geojson_data.get("features", []):
    props = feature.get("properties", {})
    if props.get("target_id") == "ABSTRACT_544":
        continue

    coords = feature.get("geometry", {}).get("coordinates", [])
    if len(coords) == 2:
        lon, lat = coords[0], coords[1]
        dist_miles = haversine_miles(CENTROID_LAT, CENTROID_LON, lat, lon)
        
        props["distance_miles"] = round(dist_miles, 3)
        
        distance_ledger.append({
            "registry_id": props.get("registry_id"),
            "facility_name": props.get("facility_name"),
            "city": props.get("city"),
            "distance_miles": round(dist_miles, 3),
            "latitude": lat,
            "longitude": lon,
            "permit_count": props.get("permit_count", 0),
            "statutes": props.get("statutes", [])
        })

distance_ledger.sort(key=lambda x: x["distance_miles"])

with open("abstract_544_facilities.geojson", "w") as out:
    json.dump(geojson_data, out, indent=2)

with open("abstract_544_distance_matrix.json", "w") as out:
    json.dump(distance_ledger, out, indent=2)

print(f"[+] Distance matrix calculated across {len(distance_ledger)} facilities relative to Abstract 544 ({CENTROID_LAT}, {CENTROID_LON}):")
print(f"    - Closest Facility:  {distance_ledger[0]['facility_name']} ({distance_ledger[0]['distance_miles']} mi)")
print(f"    - Furthest Facility: {distance_ledger[-1]['facility_name']} ({distance_ledger[-1]['distance_miles']} mi)")
print(f"    - Saved Matrix:      abstract_544_distance_matrix.json")
print(f"    - Updated GeoJSON:    abstract_544_facilities.geojson")
