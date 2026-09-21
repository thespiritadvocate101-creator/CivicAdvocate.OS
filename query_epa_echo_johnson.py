import os
import json
import time
import requests
import geopandas as gpd
from shapely.geometry import Point, box

def fetch_program_facilities(service_prefix):
    base_url = "https://echodata.epa.gov/echo/"
    url = f"{base_url}{service_prefix}.get_facilities"
    
    params = {
        "p_st": "TX",
        "p_co": "Johnson",
        "output": "JSON"
    }
    
    print(f"Querying {service_prefix} for Johnson County, TX...")
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"API connection error on {service_prefix}: {e}")
        return []
    
    data = response.json()
    results = data.get("Results", {})
    facilities = results.get("Facilities", [])
    qid = results.get("QueryID") or results.get("QID")
    
    if qid and not facilities:
        qid_url = f"{base_url}{service_prefix}.get_qid"
        qid_params = {
            "qid": qid,
            "output": "JSON",
            "pageno": 1,
            "count": 1000
        }
        time.sleep(1)
        try:
            qid_resp = requests.get(qid_url, params=qid_params, timeout=30)
            qid_resp.raise_for_status()
            facilities = qid_resp.json().get("Results", {}).get("Facilities", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching QID results for {service_prefix}: {e}")
            
    print(f"Retrieved {len(facilities)} facilities from {service_prefix}.")
    return facilities

def fetch_epa_echo_johnson_county():
    programs = ["cwa_rest_services", "rcra_rest_services", "air_rest_services"]
    all_facilities = []
    
    for prog in programs:
        facs = fetch_program_facilities(prog)
        for f in facs:
            f["SourceProgram"] = prog
        all_facilities.extend(facs)
        
    print(f"Total records aggregated across all programs: {len(all_facilities)}")
    return all_facilities

def ensure_boundary_file():
    boundary_path = "abstract_544.geojson"
    if os.path.exists(boundary_path):
        return boundary_path
        
    print(f"Notice: '{boundary_path}' not found. Generating default Johnson County bounding box polygon...")
    poly = box(-97.5, 32.2, -97.1, 32.6)
    gdf = gpd.GeoDataFrame(
        [{"id": 544, "survey_name": "Abstract 544 Johnson County", "geometry": poly}],
        crs="EPSG:4326"
    )
    gdf.to_file(boundary_path, driver="GeoJSON")
    print(f"Created fallback boundary file: {boundary_path}")
    return boundary_path

def process_spatial_overlay(facilities):
    if not facilities:
        print("Skipping spatial overlay: No facility records available to process.")
        return
        
    records = []
    seen_ids = set()
    
    for fac in facilities:
        try:
            lat, lon = None, None
            
            # Heuristic scan: Search every field for values falling within Johnson County bounds
            for k, val in fac.items():
                if val in [None, "", "null"]:
                    continue
                try:
                    f_val = float(val)
                    if 31.5 <= f_val <= 33.5 and lat is None:
                        lat = f_val
                    elif -98.5 <= f_val <= -96.5 and lon is None:
                        lon = f_val
                except (ValueError, TypeError):
                    continue
            
            # Fallback explicit key lookup if needed
            if lat is None or lon is None:
                for lkey in ["Latitude", "LAT", "FacLat", "FAC_LAT", "Y", "LATITUDE", "CWP_LAT"]:
                    if fac.get(lkey):
                        try:
                            lat = float(fac.get(lkey))
                            break
                        except ValueError:
                            pass
                for lkey in ["Longitude", "LON", "FacLong", "FAC_LONG", "X", "LONGITUDE", "CWP_LONG"]:
                    if fac.get(lkey):
                        try:
                            lon = float(fac.get(lkey))
                            break
                        except ValueError:
                            pass

            if lat is None or lon is None or not (31.5 <= lat <= 33.5 and -98.5 <= lon <= -96.5):
                continue
                
            frs_id = (
                fac.get("SourceID") or 
                fac.get("FRS_ID") or 
                fac.get("RegistryID") or 
                fac.get("FacilityID") or 
                fac.get("SourceId") or
                fac.get("MasterExternalPermitNmbr")
            )
            if frs_id in seen_ids:
                continue
            if frs_id:
                seen_ids.add(frs_id)
                
            fac_name = (
                fac.get("FacilityName") or 
                fac.get("PRIMARY_NAME") or 
                fac.get("FAC_NAME") or 
                fac.get("Facility_Name") or 
                fac.get("CWPName") or 
                fac.get("RCRAName") or
                "Unknown Facility"
            )
            
            records.append({
                "frs_id": str(frs_id),
                "facility_name": str(fac_name),
                "program_system": fac.get("SourceProgram"),
                "geometry": Point(lon, lat)
            })
        except (TypeError, ValueError):
            continue
            
    print(f"Successfully mapped coordinates for {len(records)} out of {len(facilities)} records.")
    if not records:
        print("Warning: Coordinate parsing failed.")
        return

    facilities_gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
    
    boundary_path = ensure_boundary_file()
    survey_boundary = gpd.read_file(boundary_path)
    
    if facilities_gdf.crs != survey_boundary.crs:
        facilities_gdf = facilities_gdf.to_crs(survey_boundary.crs)
        
    matched = gpd.sjoin(facilities_gdf, survey_boundary, how="inner", predicate="within")
    
    output_filename = "abstract_544_epa_echo_matches.geojson"
    matched.to_file(output_filename, driver="GeoJSON")
    print(f"Success: Matched {len(matched)} regulated facilities within survey boundary.")
    print(f"Geospatial export completed: {output_filename}")

if __name__ == "__main__":
    facility_data = fetch_epa_echo_johnson_county()
    process_spatial_overlay(facility_data)
