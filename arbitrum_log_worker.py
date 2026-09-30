#!/usr/bin/env python3
import time
import logging
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import execute_values
from web3 import Web3

# --- CONFIGURATION ---
ARBITRUM_RPC_URL = "https://arb1.arbitrum.io/rpc"  # Replace with dedicated RPC if needed
DB_NAME = "civicadvocate_db"
POLL_INTERVAL_SECONDS = 5
BLOCK_CHUNK_SIZE = 100  # Number of blocks to fetch per RPC call

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Connect to Web3
w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC_URL))

def get_db_connection():
    """Returns a connection to local PostgreSQL server."""
    return psycopg2.connect(dbname=DB_NAME)

def insert_logs_batch(conn, logs: List[Dict[str, Any]]) -> int:
    """Inserts a batch of raw EVM log objects using execute_values."""
    if not logs:
        return 0

    query = """
        INSERT INTO arbitrum_raw_logs (
            block_number,
            block_hash,
            transaction_hash,
            transaction_index,
            log_index,
            address,
            topic0,
            topic1,
            topic2,
            topic3,
            data,
            removed
        ) VALUES %s
        ON CONFLICT (block_number, transaction_hash, log_index) 
        DO NOTHING;
    """

    records = []
    for log in logs:
        topics = log.get("topics", [])
        records.append((
            log["blockNumber"],
            log["blockHash"].hex(),
            log["transactionHash"].hex(),
            log["transactionIndex"],
            log["logIndex"],
            log["address"].lower(),
            topics[0].hex() if len(topics) > 0 else None,
            topics[1].hex() if len(topics) > 1 else None,
            topics[2].hex() if len(topics) > 2 else None,
            topics[3].hex() if len(topics) > 3 else None,
            log.get("data", ""),
            log.get("removed", False)
        ))

    with conn.cursor() as cursor:
        execute_values(cursor, query, records)
        conn.commit()

    return len(records)

def main():
    if not w3.is_connected():
        logging.error("Failed to connect to Arbitrum RPC node.")
        return

    logging.info(f"Connected to Arbitrum via {ARBITRUM_RPC_URL}")
    
    conn = get_db_connection()
    
    # Determine the latest processed block stored in PostgreSQL
    with conn.cursor() as cursor:
        cursor.execute("SELECT MAX(block_number) FROM arbitrum_raw_logs;")
        result = cursor.fetchone()
        last_processed_block = result[0] if result[0] else None

    # Default to recent blocks if starting fresh
    if last_processed_block is None:
        latest_network_block = w3.eth.block_number
        last_processed_block = latest_network_block - 50
        logging.info(f"No previous blocks found. Starting from block {last_processed_block}")

    while True:
        try:
            latest_block = w3.eth.block_number

            if last_processed_block >= latest_block:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            from_block = last_processed_block + 1
            to_block = min(from_block + BLOCK_CHUNK_SIZE - 1, latest_block)

            logging.info(f"Fetching logs from block {from_block} to {to_block}...")

            # Query RPC for event logs across all contracts in range
            logs = w3.eth.get_logs({
                "fromBlock": from_block,
                "toBlock": to_block
            })

            inserted_count = insert_logs_batch(conn, logs)
            logging.info(f"Processed blocks {from_block}..{to_block} | Logs ingested: {inserted_count}")

            last_processed_block = to_block

        except Exception as e:
            logging.error(f"Error during ingestion cycle: {e}")
            # Reconnect DB if connection died
            try:
                conn = get_db_connection()
            except Exception:
                pass
            time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
