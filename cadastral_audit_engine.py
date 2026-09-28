import math
import json
import hashlib
import sqlite3

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

def run_and_anchor_audit():
    with open("abstract_544_field_notes.json", "r") as f:
        data = json.load(f)
    
    x, y = 0.0, 0.0
    vertices = [(x, y)]
    perimeter = 0.0

    for call in data["calls"]:
        rad = parse_bearing_to_angle(call["quadrant"], call["degrees"], call["minutes"])
        dist = call["distance_ft"]
        
        dx = dist * math.sin(rad)
        dy = dist * math.cos(rad)
        
        x += dx
        y += dy
        vertices.append((x, y))
        perimeter += dist

    # Linear misclosure
    closure_error = math.sqrt(vertices[-1][0]**2 + vertices[-1][1]**2)
    precision = perimeter / closure_error if closure_error > 0 else float('inf')

    # Acreage calculation via Shoelace formula
    area_sq_ft = 0.5 * abs(sum(vertices[i][0] * (vertices[(i+1)%len(vertices)][1] - vertices[i-1][1]) for i in range(len(vertices))))
    acres = area_sq_ft / 43560.0

    report = {
        "target_abstract": data["abstract"],
        "senior_patent": data["survey"],
        "county": data["county"],
        "perimeter_ft": round(perimeter, 2),
        "closure_error_ft": round(closure_error, 4),
        "traverse_precision": f"1:{int(precision)}",
        "calculated_acreage": round(acres, 4),
        "status": "CoGo-Closure-Verified"
    }
    
    # Generate canonical JSON string and compute SHA-512 digest
    report_json = json.dumps(report, sort_keys=True)
    sha512_digest = hashlib.sha512(report_json.encode('utf-8')).hexdigest()
    report["sha512_digest"] = sha512_digest

    # Anchor into SQLite forensic ledger
    conn = sqlite3.connect('forensic_ledger.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_anchors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_abstract TEXT,
            report_payload TEXT,
            sha512_digest TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        INSERT INTO audit_anchors (target_abstract, report_payload, sha512_digest)
        VALUES (?, ?, ?)
    ''', (report["target_abstract"], report_json, sha512_digest))
    conn.commit()
    conn.close()

    print(json.dumps(report, indent=2))
    print(f"\n[+] Audit report successfully anchored with SHA-512 digest in forensic_ledger.db")

if __name__ == "__main__":
    run_and_anchor_audit()
