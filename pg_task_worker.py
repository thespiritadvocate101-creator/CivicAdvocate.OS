import os
import sys
import time
import json
import hashlib
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("pg_task_worker")

DB_DSN = os.getenv("DATABASE_URL", "postgresql://localhost:5432/civic_advocate")
MAX_RETRIES = 3
POLL_INTERVAL_SECONDS = 5

def get_db_connection():
    return psycopg2.connect(DB_DSN, cursor_factory=RealDictCursor)

def compute_sha512(data_str: str) -> str:
    return hashlib.sha512(data_str.encode("utf-8")).hexdigest()

def process_task(cursor, task):
    task_id = task["id"]
    payload = task["payload"]
    chain_id = payload.get("chain_id")
    tx_hash = payload.get("tx_hash")
    block_number = payload.get("block_number")
    log_index = payload.get("log_index", 0)
    contract_address = payload.get("contract_address")
    topic_signature = payload.get("topic_signature")
    
    payload_json = json.dumps(payload)
    sha512_digest = compute_sha512(payload_json)

    cursor.execute(
        """
        INSERT INTO chain_event_logs (
            chain_id, tx_hash, block_number, log_index, 
            contract_address, topic_signature, payload_data, sha512_digest
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (chain_id, tx_hash, log_index) DO NOTHING;
        """,
        (
            chain_id, tx_hash, block_number, log_index,
            contract_address, topic_signature, payload_json, sha512_digest
        )
    )

def worker_loop():
    logger.info("Starting PostgreSQL multi-chain task worker...")
    while True:
        conn = None
        try:
            conn = get_db_connection()
            conn.autocommit = False
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, payload, attempts, max_retries 
                    FROM task_queue 
                    WHERE status = 'PENDING' 
                    ORDER BY created_at ASC 
                    LIMIT 1 
                    FOR UPDATE SKIP LOCKED;
                    """
                )
                task = cur.fetchone()

                if not task:
                    conn.commit()
                    time.sleep(POLL_INTERVAL_SECONDS)
                    continue

                task_id = task["id"]
                attempts = task["attempts"] + 1
                max_retries = task["max_retries"]

                try:
                    process_task(cur, task)
                    cur.execute(
                        "UPDATE task_queue SET status = 'COMPLETED', updated_at = NOW() WHERE id = %s;",
                        (task_id,)
                    )
                    conn.commit()
                    logger.info(f"Successfully processed task ID {task_id}")
                except Exception as inner_e:
                    conn.rollback()
                    logger.error(f"Error processing task ID {task_id} (Attempt {attempts}/{max_retries}): {inner_e}")
                    
                    with conn.cursor() as err_cur:
                        if attempts >= max_retries:
                            err_cur.execute(
                                """
                                UPDATE task_queue 
                                SET status = 'FAILED_DLQ', attempts = %s, updated_at = NOW() 
                                WHERE id = %s;
                                """,
                                (attempts, task_id)
                            )
                            err_cur.execute(
                                """
                                INSERT INTO dlq_chain_logs (task_id, payload, error_message) 
                                VALUES (%s, %s, %s);
                                """,
                                (task_id, json.dumps(task["payload"]), str(inner_e))
                            )
                            logger.warning(f"Task ID {task_id} moved to Dead-Letter Queue.")
                        else:
                            err_cur.execute(
                                """
                                UPDATE task_queue 
                                SET status = 'PENDING', attempts = %s, updated_at = NOW() 
                                WHERE id = %s;
                                """,
                                (attempts, task_id)
                            )
                        conn.commit()

        except Exception as db_e:
            logger.error(f"Database connection or outer loop error: {db_e}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            time.sleep(POLL_INTERVAL_SECONDS)
        finally:
            if conn:
                conn.close()

if __name__ == "__main__":
    try:
        worker_loop()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
        sys.exit(0)
