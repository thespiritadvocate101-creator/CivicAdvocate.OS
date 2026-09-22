import json
import folium
from folium import GeoJson, GeoJsonPopup, GeoJsonTooltip, LayerControl

# 1. Define sample/mock GeoJSON data representing Abstract 544 survey tracts & compliance audits
# (You can replace this dictionary loader with: with open('abstract_544.geojson') as f: data = json.load(f))
gis_data = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-97.3850, 32.4200],
                        [-97.3700, 32.4200],
                        [-97.3700, 32.4050],
                        [-97.3850, 32.4050],
                        [-97.3850, 32.4200]
                    ]
                ]
            },
            "properties": {
                "tract_id": "Abstract 544 - Tract A",
                "survey": "Johnson County Survey",
                "status": "Compliant",
                "risk_score": "Low",
                "ledger_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-97.4020, 32.4350],
                        [-97.3880, 32.4350],
                        [-97.3880, 32.4220],
                        [-97.4020, 32.4220],
                        [-97.4020, 32.4350]
                    ]
                ]
            },
            "properties": {
                "tract_id": "Abstract 544 - Tract B (EPA Cross-Check)",
                "survey": "Johnson County Survey",
                "status": "Review Required",
                "risk_score": "Elevated",
                "ledger_hash": "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce"
            }
        }
    ]
}

# 2. Initialize the Folium map centered over the target area (Johnson County / Burleson region)
m = folium.Map(
    location=[32.42, -97.38],
    zoom_start=13,
    tiles="CartoDB positron"  # Clean, modern base map tiles
)

# 3. Define conditional styling based on audit status properties
def style_function(feature):
    status = feature["properties"].get("status")
    if status == "Compliant":
        color = "#2ecc71"  # Green
    else:
        color = "#e74c3c"  # Red/Orange warning
    
    return {
        "fillColor": color,
        "color": "#2c3e50",
        "weight": 2,
        "fillOpacity": 0.4
    }

# Highlight style when hovering over boundaries
highlight_function = lambda x: {"weight": 4, "fillOpacity": 0.7}

# 4. Create tooltips (appears on hover)
tooltip = GeoJsonTooltip(
    fields=["tract_id", "status"],
    aliases=["Tract:", "Audit Status:"],
    localize=True,
    sticky=True,
    labels=True,
    style="background-color: #ffffff; color: #333333; font-family: sans-serif; font-size: 12px; padding: 6px; border-radius: 4px; box-shadow: 2px 2px 6px rgba(0,0,0,0.2);"
)

# 5. Create popups (appears on click)
popup = GeoJsonPopup(
    fields=["tract_id", "survey", "status", "risk_score", "ledger_hash"],
    aliases=["Tract Name:", "Survey:", "Status:", "Risk Level:", "SHA-512 Hash:"],
    localize=True,
    labels=True,
    max_width=400,
    style="background-color: #fdfdfd; font-family: sans-serif; font-size: 11px; padding: 8px;"
)

# 6. Add the GeoJSON layer to the map
GeoJson(
    gis_data,
    name="Abstract 544 Boundaries",
    style_function=style_function,
    highlight_function=highlight_function,
    tooltip=tooltip,
    popup=popup
).add_to(m)

# 7. Add Layer Control panel to toggle layers dynamically
LayerControl().add_to(m)

# 8. Save the output map to an HTML file ready for local hosting
output_filename = "abstract_544_map.html"
m.save(output_filename)
print(f"Interactive GIS map successfully compiled and saved to {output_filename}")

