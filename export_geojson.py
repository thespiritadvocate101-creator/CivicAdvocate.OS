import math
import json

def parse_bearing_to_angle(quadrant, degrees, minutes):
    total_deg = degrees + (minutes / 60.0)
    if quadrant == "NE":
        return math.radians(total_deg)
    elif quadrant == "SE":
        return math.radians(180.0 - total_deg)
    elif quadrant == "SW":
        return math.radians(180.0 + total_deg)
    elif quadrant == "NW":
        return math.radians(360.0 - total_deg)
    return 0.0

def generate_geojson():
    with open("abstract_544_field_notes.json", "r") as f:
        data = json.load(f)

    # Anchor point in Johnson County, Texas (approximate base coordinates)
    base_lat = 32.4200
    base_lon = -97.3800
    
    # Conversion factors for feet to degrees at ~32.4° N
    # 1 degree latitude ≈ 364,000 feet
    # 1 degree longitude ≈ 307,000 feet
    ft_per_deg_lat = 364000.0
    ft_per_deg_lon = 307000.0

    x, y = 0.0, 0.0
    local_coords = [(x, y)]

    for call in data["calls"]:
        rad = parse_bearing_to_angle(call["quadrant"], call["degrees"], call["minutes"])
        dist = call["distance_ft"]
        
        dx = dist * math.sin(rad)
        dy = dist * math.cos(rad)
        
        x += dx
        y += dy
        local_coords.append((x, y))

    # Convert local Cartesian feet to WGS84 lon/lat polygon ring
    polygon_ring = []
    for lx, ly in local_coords:
        lon = base_lon + (lx / ft_per_deg_lon)
        lat = base_lat + (ly / ft_per_deg_lat)
        polygon_ring.append([round(lon, 6), round(lat, 6)])

    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [polygon_ring]
                },
                "properties": {
                    "target_abstract": data["abstract"],
                    "senior_patent": data["survey"],
                    "county": data["county"],
                    "status": "GeoJSON-Spatial-Polygon-Exported"
                }
            }
        ]
    }

    with open("abstract_544_boundary.geojson", "w") as out:
        json.dump(geojson_data, out, indent=2)

    print(json.dumps(geojson_data, indent=2))
    print("\n[+] Spatial polygon successfully exported to abstract_544_boundary.geojson")

if __name__ == "__main__":
    generate_geojson()
