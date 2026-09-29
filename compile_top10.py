import json

with open("abstract_544_distance_matrix.json") as f:
    data = json.load(f)

top10 = data[:10]

md_lines = [
    "### Top 10 Closest Facilities to Abstract 544 Centroid (32.42, -97.38)",
    "",
    "| Rank | Registry ID | Facility Name | City | Distance (mi) | Permits | Program Statutes |",
    "| :---: | :---: | :--- | :--- | :---: | :---: | :--- |"
]

for idx, fac in enumerate(top10, start=1):
    reg_id = fac.get("registry_id", "N/A")
    name = fac.get("facility_name", "N/A")
    city = fac.get("city", "N/A")
    dist = fac.get("distance_miles", 0.0)
    permits = fac.get("permit_count", 0)
    statutes = ", ".join(fac.get("statutes", [])) or "FRS / Unassigned"
    
    md_lines.append(f"| {idx} | `{reg_id}` | {name} | {city} | {dist:.3f} | {permits} | {statutes} |")

markdown_output = "\n".join(md_lines)

print(markdown_output)

with open("top_10_closest_facilities.md", "w") as out:
    out.write(markdown_output + "\n")

print("\n[+] Top 10 proximity report compiled and saved to top_10_closest_facilities.md")
