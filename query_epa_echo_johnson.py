import os
import time
import requests
import geopandas as gpd
from shapely.geometry import Point

def fetch_epa_echo_johnson_county():
    base_url = "https://echodata.epa.gov/echo/"
    
    # Target parameters for Johnson County, TX (FIPS: 48251)
    params = {
        "p_st": "TX",
        "p_fips": "48251",
        "output": "JSON"
    }
    
    print("Initializing query with EPA ECHO Combined Data REST services...")
    init_url = base_url + "combined_data.get_facilities"
    
    try:
        response = requests.get(init_url, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"API connection error during initialization: {e}")
        return []
    
    data = response.json()
    results = data.get("Results", {})
    
    # Check if a Query ID (QID) was returned for pagination/retrieval
    qid = results.get("QueryID") or results.get("QID")
    facilities = results.get("Facilities", [])
    
    if qid and not facilities:
        print(f"Received Query ID: {qid}. Fetching facility records...")
        qid_url = base_url + "combined_data.get_qid"
        qid_params = {
            "qid": qid,
            "output": "JSON",
            "pageno": 1,
            "count": 100
        }
        time.sleep(1)
        try:
            qid_response = requests.get(qid_url, params=qid_params, timeout=30)
            qid_response.raise_for_status()
            qid_data = qid_response.json()
            facilities = qid_data.get("Results", {}).get("Facilities", [])
        except requests.exceptions.RequestException as e:
            print(f"API connection error while fetching QID results: {e}")
            return []

    if not facilities:
        # Fallback: try direct state query filtered locally for Johnson County
        print("County-specific filter returned no records. Attempting state-wide query for TX to filter locally...")
        fallback_params = {"p_st": "TX", "output": "JSON"}
        try:
            fb_response = requests.get(init_url, params=fallback_params, timeout=30)
            fb_data = fb_response.json()
            fb_results = fb_data.get("Results", {})
            fb_qid = fb_results.get("QueryID") or fb_results.get("QID")
            if fb_qid:
                time.sleep(1)
                fb_qid_response = requests.get(base_url + "combined_data.get_qid", params={"qid": fb_qid, "output": "JSON", "pageno": 1, "count": 500}, timeout=30)
                all_tx_facilities = fb_qid_response.json().get("Results", {}).get("Facilities", [])
                # Filter locally for Johnson County (case-insensitive)
                facilities = [f for f in all_tx_facilities if str(f.get("County", "")).strip().lower() == "johnson"]
        except Exception as e:
            print(f"Fallback query error: {e}")

    print(f"Retrieved {len(facilities)} regulated facilities for Johnson County.")
    return facilities

def process_spatial_overlay(facilities, survey_boundary_path="abstract_544.geojson"):
    if not facilities:
        print("Skipping spatial overlay: No facility records available to process.")
        return
        
    records = []
    for fac in facilities:
        try:
            lat = float(fac.get("Latitude") or fac.get("LAT"))
            lon = float(fac.get("Longitude") or fac.get("LON"))
            records.append({
                "frs_id": fac.get("SourceID") or fac.get("FRS_ID") or fac.get("RegistryID"),
                "facility_name": fac.get("FacilityName") or fac.get("PRIMARY_NAME"),
                "program_system": fac.get("SourceSystem") or fac.get("PROGRAM"),
                "geometry": Point(lon, lat)
            })
        except (TypeError, ValueError):
            continue
            
    if not records:
        print("Warning: Facilities found, but none contained valid latitude/longitude coordinates.")
        return

    facilities_gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
    
    if not os.path.exists(survey_boundary_path):
        print(f"Error: Survey boundary file '{survey_boundary_path}' not found in current directory.")
        return
        
    survey_boundary = gpd.read_file(survey_boundary_path)
    
    if facilities_gdf.crs != survey_boundary.crs:
        facilities_gdf = facilities_gdf.to_crs(survey_boundary.crs)
        
    matched = gpd.sjoin(facilities_gdf, survey_boundary, how="inner", predicate="within")
    
    output_filename = "abstract_544_epa_echo_matches.geojson"
    matched.to_file(output_filename, driver="GeoJSON")
    print(f"Success: Matched {len(matched)} regulated facilities within Abstract 544 boundary.")
    print(f"Geospatial export completed: {output_filename}")

if __name__ == "__main__":
    facility_data = fetch_epa_echo_johnson_county()
    process_spatial_overlay(facility_data)
