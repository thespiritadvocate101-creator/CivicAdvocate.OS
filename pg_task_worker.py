import psycopg2
from psycopg2.extras import RealDictCursor, Json
import subprocess, os, time, json, hashlib

PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5432")
PG_DB   = os.getenv("PGDATABASE", "civicadvocate")
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASS = os.getenv("PGPASSWORD", "")
WORKER_ID = f"worker_{os.getpid()}"

def fetch_and_lock_task(cursor):
    query = """
    WITH next_task AS (
        SELECT id FROM task_queue
        WHERE status = 'PENDING'
        ORDER BY id ASC
        FOR UPDATE SKIP LOCKED LIMIT 1
    )
    UPDATE task_queue SET status = 'PROCESSING'
    FROM next_task WHERE task_queue.id = next_task.id
    RETURNING task_queue.id, task_queue.task_type, task_queue.task_payload;
    """
    cursor.execute(query)
    return cursor.fetchone()

def mark_completed(cursor, task_id):
    cursor.execute("UPDATE task_queue SET status = 'COMPLETED' WHERE id = %s;", (task_id,))

def mark_failed(cursor, task_id):
    cursor.execute("UPDATE task_queue SET status = 'FAILED' WHERE id = %s;", (task_id,))

def run_worker_loop():
    print(f"[{WORKER_ID}] Master Engine active. Polling task_queue...")
    pg_conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS)
    pg_conn.autocommit = False

    script_map = {
        'SPATIAL_AUDIT_SYNC': 'query_epa_echo_johnson.py',
        'epa_echo_compliance_sync': 'query_epa_echo_johnson.py',
        'jcad_certified_roll_sync': 'parse_patent.py',
        'jcad_gis_boundary_sync': 'compute_acreage.py',
        'rrc_infrastructure_sync': 'query_rrc_johnson.py',
        'cleburne_municipal_gis_sync': 'echo_placeholder'
    }

    try:
        while True:
            with pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                task = fetch_and_lock_task(cursor)
                if task:
                    task_id = task['id']
                    task_type = task['task_type']
                    task_payload = task.get('task_payload') or {}
                    
                    # Define target entity early for scoping safety
                    target_entity = task_payload.get('target', 'Abstract 544')
                    print(f"[{WORKER_ID}] Claimed Task ID: {task_id} ({task_type}) for target: {target_entity}")

                    if task_type in script_map:
                        target_script = script_map[task_type]
                        live_data = "{}"
                        geo_audit_result = "{}"
                        
                        # VECTOR 1: Live API Extraction
                        if target_script != 'echo_placeholder' and os.path.exists(target_script):
                            print(f"[{WORKER_ID}] Executing Live API extraction via {target_script}...")
                            api_res = subprocess.run(["python3", target_script], capture_output=True, text=True)
                            live_data = api_res.stdout.strip() if api_res.returncode == 0 else f"Error: {api_res.stderr.strip()}"
                        else:
                            print(f"[{WORKER_ID}] Script {target_script} pending. Using diagnostic placeholder.")
                            live_data = '{"diagnostic": "Awaiting active script integration"}'

                        # VECTOR 2: Geospatial Cross-Referencing against Dynamic Target
                        if os.path.exists("proximity_audit.py"):
                            print(f"[{WORKER_ID}] Cross-referencing against {target_entity}...")
                            geo_res = subprocess.run(["python3", "proximity_audit.py", "--target", target_entity], input=live_data, capture_output=True, text=True)
                            geo_audit_result = geo_res.stdout.strip() if geo_res.returncode == 0 else f"Error: {geo_res.stderr.strip()}"
                        else:
                            geo_audit_result = '{"diagnostic": "proximity_audit.py not found in working directory."}'

                        # Assemble Unified Payload
                        gathered_data = {
                            "status": "spatially_audited",
                            "jurisdiction": task_payload.get("jurisdiction", "Johnson County"),
                            "target_entity": target_entity,
                            "live_api_telemetry": live_data,
                            "cadastral_variance_report": geo_audit_result
                        }
                        
                        # Cryptographic Sealing
                        data_string = json.dumps(gathered_data, sort_keys=True).encode('utf-8')
                        sha512_digest = hashlib.sha512(data_string).hexdigest()
                        
                        cursor.execute("""
                            INSERT INTO audit_result_ledger (source_task_id, target_entity, gathered_data, sha512_digest)
                            VALUES (%s, %s, %s, %s)
                        """, (task_id, target_entity, json.dumps(gathered_data), sha512_digest))
                        print(f"[{WORKER_ID}] Sealed {task_type} variance report for {target_entity} with SHA-512.")
                        
                        mark_completed(cursor, task_id)
                    else:
                        print(f"[{WORKER_ID}] Unknown task type. Marking failed.")
                        mark_failed(cursor, task_id)

                    pg_conn.commit()
                else:
                    pg_conn.rollback()
                    time.sleep(2)
    except KeyboardInterrupt:
        print(f"\n[{WORKER_ID}] Worker process stopped.")
    finally:
        pg_conn.close()

if __name__ == "__main__":
    run_worker_loop()
