#!/usr/bin/env bash
# ==============================================================================
# CivicAdvocate.OS - GIS Pipeline & PostgreSQL Ledger Integration Script
# ==============================================================================
set -e

echo "[*] Initializing GIS mapping pipeline..."

# 1. Ensure required Python packages are installed
python3 -c "import folium, psycopg2, json" 2>/dev/null || {
    echo "[*] Installing required Python packages..."
    pip install folium psycopg2-binary
}

# 2. Execute Python processing pipeline via heredoc
python3 - << 'EOF_PY'
import json
import os
import psycopg2
from folium import Map, GeoJson, GeoJsonPopup, GeoJsonTooltip, LayerControl

db_name = os.getenv("POSTGRES_DB", "civic_cadastral_audit")
db_user = os.getenv("POSTGRES_USER", "postgres")
db_host = os.getenv("POSTGRES_HOST", "localhost")

ledger_data = {}

try:
    conn = psycopg2.connect(dbname=db_name, user=db_user, host=db_host)
    cursor = conn.cursor()
    cursor.execute("SELECT tract_id, status, risk_score, ledger_hash FROM audit_ledger;")
    rows = cursor.fetchall()
    for row in rows:
        ledger_data[str(row[0])] = {
            "status": row[1],
            "risk_score": row[2],
            "ledger_hash": row[3]
        }
    cursor.close()
    conn.close()
    print("[+] Successfully synchronized records from PostgreSQL audit ledger.")
except Exception as e:
    print(f"[!] Notice: PostgreSQL ledger connection skipped ({e}). Using GeoJSON attributes.")

# Load Abstract 544 GeoJSON file
geojson_path = "abstract_544.geojson"
if os.path.exists(geojson_path):
    with open(geojson_path, "r") as f:
        gis_data = json.load(f)
    print(f"[+] Loaded spatial boundaries from {geojson_path}")
else:
    raise FileNotFoundError(f"[!] Critical: {geojson_path} not found in execution directory.")

# Standardize feature properties to prevent KeyError/AssertionError
for feature in gis_data.get("features", []):
    props = feature.setdefault("properties", {})
    
    # Map existing keys flexibly
    t_id = props.get("tract_id") or props.get("id") or "Unknown Tract"
    props["tract_id"] = t_id
    props.setdefault("survey", props.get("survey_name", "Johnson County Survey"))
    props.setdefault("status", "Compliant")
    props.setdefault("risk_score", "Standard")
    props.setdefault("ledger_hash", "Pending Ledger Verification")
    
    # Overwrite with live ledger data if available
    if str(t_id) in ledger_data:
        props.update(ledger_data[str(t_id)])

# Initialize Map centered over Johnson County / Burleson region
m = Map(
    location=[32.42, -97.38],
    zoom_start=13,
    tiles="OpenStreetMap"
)

# Dynamic styling based on status property
def style_function(feature):
    status = feature["properties"].get("status", "Compliant")
    color = "#2ecc71" if "Compliant" in str(status) else "#e74c3c"
    return {
        "fillColor": color,
        "color": "#2c3e50",
        "weight": 2,
        "fillOpacity": 0.4
    }

highlight_function = lambda x: {"weight": 4, "fillOpacity": 0.7}

# Tooltips and Popups mapped to safe property keys
tooltip = GeoJsonTooltip(
    fields=["tract_id", "status"],
    aliases=["Tract:", "Status:"],
    localize=True,
    sticky=True,
    labels=True,
    style="background-color: #ffffff; color: #333333; font-family: sans-serif; font-size: 12px; padding: 6px; border-radius: 4px;"
)

popup = GeoJsonPopup(
    fields=["tract_id", "survey", "status", "risk_score", "ledger_hash"],
    aliases=["Tract:", "Survey:", "Status:", "Risk:", "SHA-512 Hash:"],
    localize=True,
    labels=True,
    max_width=400,
    style="background-color: #fdfdfd; font-family: sans-serif; font-size: 11px; padding: 8px;"
)

GeoJson(
    gis_data,
    name="Abstract 544 Audit Boundaries",
    style_function=style_function,
    highlight_function=highlight_function,
    tooltip=tooltip,
    popup=popup
).add_to(m)

LayerControl().add_to(m)

output_file = "abstract_544_map.html"
m.save(output_file)
print(f"[+] Interactive GIS map successfully compiled to {output_file}")
EOF_PY

echo "[*] Pipeline execution complete."
