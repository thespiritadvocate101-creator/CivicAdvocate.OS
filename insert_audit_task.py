import psycopg2
import json

try:
    conn = psycopg2.connect(dbname="postgres", user="u0_a540", host="localhost", port=5432)
    cursor = conn.cursor()
    
    task_payload = json.dumps({
        "priority": "HIGH",
        "senior_patent": "Silas Elbert Bandy",
        "genesis_anchor": "CIVICADVOCATE.OS-V6",
        "target_abstract": "Abstract 544",
        "target_database": "civic_cadastral_audit",
        "subsystem_context": "Scheduled-Audit-Cycle"
    })
    
    cursor.execute(
        "INSERT INTO task_queue (task_payload, status, created_at) VALUES (%s, %s, NOW());",
        (task_payload, 'PENDING')
    )
    conn.commit()
    print("[✓] New audit task successfully enqueued.")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"[ERROR] Failed to insert task: {e}")
