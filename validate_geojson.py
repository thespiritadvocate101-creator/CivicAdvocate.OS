import json

def validate_geojson(filepath):
    print(f"=== GEOJSON INTEGRITY & SCHEMA VALIDATION: {filepath} ===")
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON file: {e}")
        return False

    errors = []
    warnings = []

    # 1. Top-level GeoJSON checks
    if not isinstance(data, dict):
        errors.append("Root structure must be a JSON Object.")
        return False

    if data.get("type") != "FeatureCollection":
        errors.append(f"Invalid root type: expected 'FeatureCollection', got '{data.get('type')}'")

    features = data.get("features")
    if not isinstance(features, list):
        errors.append("Missing or invalid 'features' array.")
        return False

    print(f"[+] Root Structure: Valid FeatureCollection")
    print(f"[+] Feature Count: {len(features)}")

    # 2. Feature-level structure and coordinate bounds validation
    centroid_found = False
    facility_count = 0

    for idx, feature in enumerate(features):
        if not isinstance(feature, dict):
            errors.append(f"Feature index {idx} is not a valid object.")
            continue

        if feature.get("type") != "Feature":
            errors.append(f"Feature index {idx}: Expected type 'Feature', got '{feature.get('type')}'")

        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            errors.append(f"Feature index {idx}: Missing geometry object.")
            continue

        geom_type = geometry.get("type")
        coords = geometry.get("coordinates")

        if geom_type != "Point":
            errors.append(f"Feature index {idx}: Unexpected geometry type '{geom_type}'.")

        if not isinstance(coords, list) or len(coords) < 2:
            errors.append(f"Feature index {idx}: Invalid coordinates array {coords}.")
        else:
            lon, lat = coords[0], coords[1]
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                errors.append(f"Feature index {idx}: Out-of-bounds coordinates [{lon}, {lat}].")

        props = feature.get("properties")
        if not isinstance(props, dict):
            errors.append(f"Feature index {idx}: Missing properties object.")
            continue

        # Property checks
        if props.get("target_id") == "ABSTRACT_544":
            centroid_found = True
        else:
            facility_count += 1
            required_keys = ["registry_id", "facility_name", "city", "permit_count", "statutes"]
            for key in required_keys:
                if key not in props:
                    warnings.append(f"Feature index {idx} ({props.get('facility_name', 'Unknown')}): Missing property '{key}'")

    # 3. Final summary output
    print("\n=== VALIDATION SUMMARY ===")
    print(f"[+] Facility Point Features Validated: {facility_count}")
    print(f"[+] Abstract 544 Centroid Marker Verified: {'YES' if centroid_found else 'NO'}")
    
    if warnings:
        print(f"[!] Warnings ({len(warnings)}):")
        for w in warnings[:5]:
            print(f"    - {w}")

    if errors:
        print(f"[X] Validation FAILED with {len(errors)} error(s):")
        for e in errors[:10]:
            print(f"    - {e}")
        return False

    print("[+] RESULT: GeoJSON structural integrity and schema fully validated.")
    return True

if __name__ == "__main__":
    validate_geojson("abstract_544_facilities.geojson")
