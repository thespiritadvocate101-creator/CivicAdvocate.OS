import json

# Load DFR compliance dataset and master ledger records
with open("dfr_compliance_audit.json") as f:
    dfr_data = json.load(f)

with open("abstract_544_compliance_ledger.json") as f:
    ledger_data = {item["RegistryId"]: item for item in json.load(f)}

features = []
missing_coords = 0

for item in dfr_data:
    reg_id = item.get("RegistryId")
    name = item.get("FacilityName")
    city = item.get("City")
    dfr = item.get("DFR_Data", {})
    
    ledger_item = ledger_data.get(reg_id, {})
    statutes = ledger_item.get("Statutes", [])
    permit_count = ledger_item.get("PermitCount", 0)
    
    lat = None
    lon = None
    
    # Extract latitude and longitude from DFR permits or spatial metadata
    permits = dfr.get("Permits", []) if isinstance(dfr.get("Permits"), list) else []
    for p in permits:
        if isinstance(p, dict):
            p_lat = p.get("Latitude")
            p_lon = p.get("Longitude")
            if p_lat and p_lon:
                try:
                    lat = float(p_lat)
                    lon = float(p_lon)
                    break
                except ValueError:
                    continue
                    
    if lat is None or lon is None:
        missing_coords += 1
        continue
        
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]  # GeoJSON standard: [longitude, latitude]
        },
        "properties": {
            "registry_id": reg_id,
            "facility_name": name,
            "city": city,
            "permit_count": permit_count,
            "statutes": statutes
        }
    }
    features.append(feature)

# Abstract 544 Reference Centroid Feature
abstract_centroid_feature = {
    "type": "Feature",
    "geometry": {
        "type": "Point",
        "coordinates": [-97.38, 32.42]
    },
    "properties": {
        "target_id": "ABSTRACT_544",
        "name": "Silas Elbert Bandy Survey (Abstract 544) Centroid",
        "county": "Johnson County, TX",
        "type": "Survey Reference Centroid"
    }
}

features.insert(0, abstract_centroid_feature)

geojson_payload = {
    "type": "FeatureCollection",
    "name": "Abstract_544_Facilities_Audit_Layer",
    "crs": {
        "type": "name",
        "properties": {
            "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
        }
    },
    "features": features
}

output_filename = "abstract_544_facilities.geojson"
with open(output_filename, "w") as out:
    json.dump(geojson_payload, out, indent=2)

print(f"[+] Spatial GeoJSON FeatureCollection generated successfully:")
print(f"    - Output File: {output_filename}")
print(f"    - Facility Point Features: {len(features) - 1}")
print(f"    - Abstract 544 Reference Centroid: 1")
print(f"    - Records Missing Coordinates: {missing_coords}")
