import json

with open("abstract_544_distance_matrix.json") as f:
    distance_data = json.load(f)

top10 = distance_data[:10]

centroid_lat = 32.42
centroid_lon = -97.38

markers_js = f"""
        // Abstract 544 Centroid Marker
        var centroidIcon = L.divIcon({{
            className: 'custom-div-icon',
            html: "<div style='background-color:#e74c3c;width:18px;height:18px;border-radius:50%;border:2px solid white;'></div>",
            iconSize: [18, 18],
            iconAnchor: [9, 9]
        }});

        L.marker([{centroid_lat}, {centroid_lon}], {{icon: centroidIcon}})
            .addTo(map)
            .bindPopup("<b>Silas Elbert Bandy Survey (Abstract 544) Centroid</b><br>Coordinates: {centroid_lat}, {centroid_lon}");
"""

for idx, fac in enumerate(top10, start=1):
    reg_id = fac.get("registry_id", "N/A")
    name = fac.get("facility_name", "N/A").replace("'", "\\'")
    city = fac.get("city", "N/A")
    dist = fac.get("distance_miles", 0.0)
    lat = fac.get("latitude")
    lon = fac.get("longitude")
    permits = fac.get("permit_count", 0)
    statutes = ", ".join(fac.get("statutes", [])) or "FRS / Unassigned"

    popup_html = f"<b>#{idx}: {name}</b><br>Registry ID: {reg_id}<br>City: {city}<br>Distance: {dist} mi<br>Permits: {permits}<br>Statutes: {statutes}"

    markers_js += f"""
        L.marker([{lat}, {lon}])
            .addTo(map)
            .bindPopup('{popup_html}');
    """

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Abstract 544 - Top 10 Closest Facilities</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: sans-serif; }}
        #map {{ width: 100vw; height: 100vh; }}
        .legend {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 10px 15px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            z-index: 1000;
            font-size: 12px;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="legend">
        <strong>Abstract 544 Audit Map</strong><br>
        <span style="color:#e74c3c;">&#9679;</span> Abstract 544 Centroid<br>
        <span style="color:#357ae8;">&#9679;</span> Audited Facility Markers
    </div>
    <script>
        var map = L.map('map').setView([{centroid_lat}, {centroid_lon}], 12);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }}).addTo(map);

        {markers_js}
    </script>
</body>
</html>
"""

with open("abstract_544_top10_map.html", "w") as out:
    out.write(html_content)

print("[+] Interactive Leaflet HTML map generated: abstract_544_top10_map.html")
