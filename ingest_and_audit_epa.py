import os
import sqlite3
import hashlib
import geopandas as gpd

DB_PATH = "audit_ledger.db"
GEOJSON_PATH = "abstract_544_epa_echo_matches.geojson"

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS epa_audit_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frs_id TEXT UNIQUE,
            facility_name TEXT,
            program_system TEXT,
            latitude REAL,
            longitude REAL,
            compliance_status TEXT,
            inspection_count INTEGER,
            formal_enforcement_count INTEGER,
            record_hash TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def ingest_and_audit():
    if not os.path.exists(GEOJSON_PATH):
        print(f"Error: Target file {GEOJSON_PATH} not found.")
        return
        
    init_database()
    gdf = gpd.read_file(GEOJSON_PATH)
    
    if gdf.empty:
        print("No matched facilities found in the GeoJSON dataset to ingest.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Processing and sealing {len(gdf)} matched facilities into {DB_PATH}...")
    
    success_count = 0
    for idx, row in gdf.iterrows():
        frs_id = str(row.get("frs_id") or f"UNKNOWN_{idx}")
        name = str(row.get("facility_name") or "Unnamed Facility")
        program = str(row.get("program_system") or "cwa_rest_services")
        geom = row.get("geometry")
        
        if geom is None:
            continue
            
        lon, lat = geom.x, geom.y
        status = "Active/Reported"
        inspections = 0
        enforcements = 0
        
        # Generate SHA-512 cryptographic ledger state digest
        raw_string = f"{frs_id}:{name}:{program}:{lat}:{lon}:{status}:{inspections}:{enforcements}"
        record_hash = hashlib.sha512(raw_string.encode("utf-8")).hexdigest()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO epa_audit_ledger 
                (frs_id, facility_name, program_system, latitude, longitude, compliance_status, inspection_count, formal_enforcement_count, record_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (frs_id, name, program, lat, lon, status, inspections, enforcements, record_hash))
            success_count += 1
            if success_count % 25 == 0:
                print(f"Sealed {success_count} records...")
        except Exception as e:
            print(f"Database write error for FRS ID {frs_id}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Success: Sealed {success_count} records into the forensic ledger database.")

if __name__ == "__main__":
    ingest_and_audit()
