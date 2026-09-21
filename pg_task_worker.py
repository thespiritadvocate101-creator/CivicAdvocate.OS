import psycopg2
from psycopg2.extras import RealDictCursor, Json
import subprocess, os, time, json

PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5432")
PG_DB   = os.getenv("PGDATABASE", "civic_advocate")
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASS = os.getenv("PGPASSWORD", "postgres")
WORKER_ID = f"worker_{os.getpid()}"

def fetch_and_lock_task(cursor):
    query = """
    WITH next_task AS (
        SELECT task_id FROM task_queue
        WHERE status = 'pending' AND scheduled_at <= NOW()
        ORDER BY priority DESC, created_at ASC
        FOR UPDATE SKIP LOCKED LIMIT 1
    )
    UPDATE task_queue
    SET status = 'processing', worker_id = %s, started_at = NOW()
    FROM next_task WHERE task_queue.task_id = next_task.task_id
    RETURNING task_queue.task_id, task_queue.abstract_id, task_queue.payload, task_queue.retry_count, task_queue.max_retries;
    """
    cursor.execute(query, (WORKER_ID,))
    return cursor.fetchone()

def mark_completed(cursor, task_id):
    cursor.execute("UPDATE task_queue SET status = 'completed', completed_at = NOW() WHERE task_id = %s;", (task_id,))

def handle_failure(cursor, task):
    task_id = task['task_id']
    new_retry_count = task['retry_count'] + 1
    max_retries = task['max_retries']
    error_msg = f"Auditor binary returned non-zero exit code on worker {WORKER_ID}"
    payload_val = Json(task['payload']) if isinstance(task['payload'], dict) else task['payload']

    if new_retry_count >= max_retries:
        cursor.execute("""
            INSERT INTO dead_letter_queue (task_id, abstract_id, payload, retry_count, last_error)
            VALUES (%s, %s, %s, %s, %s);
        """, (task_id, task['abstract_id'], payload_val, new_retry_count, error_msg))
        cursor.execute("UPDATE task_queue SET status = 'dead_letter', retry_count = %s, error_log = %s, completed_at = NOW() WHERE task_id = %s;", (new_retry_count, error_msg, task_id))
        print(f"[{WORKER_ID}] TASK FAILED EXHAUSTED RETRIES -> Moved Task {task_id} to DLQ.")
    else:
        cursor.execute("UPDATE task_queue SET status = 'pending', retry_count = %s, error_log = %s WHERE task_id = %s;", (new_retry_count, error_msg, task_id))
        print(f"[{WORKER_ID}] TASK FAILED -> Incrementing retry count ({new_retry_count}/{max_retries}) for Task {task_id}.")

def run_worker_loop():
    print(f"[{WORKER_ID}] Engine active (Retry & DLQ enabled). Polling task_queue...")
    pg_conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS)
    pg_conn.autocommit = False
    try:
        while True:
            with pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                task = fetch_and_lock_task(cursor)
                if task:
                    pg_conn.commit()
                    print(f"[{WORKER_ID}] Claimed Task ID: {task['task_id']} ({task['abstract_id']})")
                    res = subprocess.run(["./dist/civic_auditor_agent"], capture_output=True, text=True)
                    if res.returncode == 0:
                        mark_completed(cursor, task['task_id'])
                        print(f"[{WORKER_ID}] Successfully completed Task ID: {task['task_id']}")
                    else:
                        handle_failure(cursor, task)
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
