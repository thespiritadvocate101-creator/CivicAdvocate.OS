import psycopg2
import hashlib
import json

# Connect to the Termux PostgreSQL socket
conn = psycopg2.connect(dbname="civic_audit", host="/data/data/com.termux/files/usr/tmp")
conn.autocommit = False
cur = conn.cursor()

# 1. Ensure the seal column exists
cur.execute("ALTER TABLE opbnb_transfers ADD COLUMN IF NOT EXISTS sha512_seal VARCHAR(128);")
conn.commit()

# 2. Fetch all unsealed records
cur.execute("""
    SELECT tx_hash, block_num, from_address, to_address, asset, value_wei 
    FROM opbnb_transfers 
    WHERE sha512_seal IS NULL 
    ORDER BY block_num ASC;
""")
unsealed_records = cur.fetchall()

if not unsealed_records:
    print("Ledger is fully sealed. No new records found.")
else:
    for record in unsealed_records:
        # Create a deterministic JSON payload for hashing
        payload_dict = {
            "tx_hash": record[0],
            "block_num": record[1],
            "from_address": record[2],
            "to_address": record[3],
            "asset": record[4],
            "value_wei": str(record[5])
        }
        # sort_keys guarantees identical JSON strings across runs
        payload_string = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))
        
        # Compute the SHA-512 digest
        seal = hashlib.sha512(payload_string.encode('utf-8')).hexdigest()
        
        # Commit the seal to the database
        cur.execute("UPDATE opbnb_transfers SET sha512_seal = %s WHERE tx_hash = %s;", (seal, record[0]))
    
    conn.commit()
    print(f"Successfully sealed {len(unsealed_records)} opBNB transfer records with SHA-512.")

cur.close()
conn.close()
