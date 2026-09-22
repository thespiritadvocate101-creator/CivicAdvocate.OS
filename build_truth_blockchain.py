import os
import time
import hashlib
import json
import psycopg2

class TruthMandateBlockchain:
    def __init__(self, db_name="civic_cadastral_audit", difficulty=2):
        self.difficulty = difficulty
        self.chain = []
        self.db_name = db_name
        self.load_or_create_genesis_block()

    def calculate_hash(self, index, previous_hash, timestamp, data, nonce):
        block_string = f"{index}{previous_hash}{timestamp}{json.dumps(data, sort_keys=True)}{nonce}"
        return hashlib.sha512(block_string.encode()).hexdigest()

    def load_or_create_genesis_block(self):
        # Genesis Block Creation
        genesis_data = {"mandate": "Truth Mandate Ledger Initialized", "author": "Brandon Lynn Campbell"}
        genesis_hash = self.calculate_hash(0, "0" * 128, int(time.time()), genesis_data, 0)
        
        genesis_block = {
            "index": 0,
            "previous_hash": "0" * 128,
            "timestamp": int(time.time()),
            "data": genesis_data,
            "nonce": 0,
            "hash": genesis_hash
        }
        self.chain.append(genesis_block)
        print("[+] Truth Mandate Genesis Block anchored with SHA-512.")

    def mine_block(self, data):
        last_block = self.chain[-1]
        index = last_block["index"] + 1
        previous_hash = last_block["hash"]
        timestamp = int(time.time())
        nonce = 0
        
        target = "0" * self.difficulty
        print(f"[*] Mining block #{index} for Truth Mandate...")
        
        while True:
            block_hash = self.calculate_hash(index, previous_hash, timestamp, data, nonce)
            if block_hash.startswith(target):
                break
            nonce += 1
            
        new_block = {
            "index": index,
            "previous_hash": previous_hash,
            "timestamp": timestamp,
            "data": data,
            "nonce": nonce,
            "hash": block_hash
        }
        self.chain.append(new_block)
        print(f"[+] Block #{index} successfully mined and sealed! Hash: {block_hash[:32]}...")
        return new_block

    def sync_from_postgres(self):
        try:
            conn = psycopg2.connect(dbname=self.db_name, user="postgres", host="localhost")
            cursor = conn.cursor()
            cursor.execute("SELECT tract_id, status, risk_score, ledger_hash FROM audit_ledger;")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if rows:
                batch_data = [{"tract_id": r[0], "status": r[1], "risk": r[2], "hash": r[3]} for r in rows]
                self.mine_block({"type": "POSTGRES_LEDGER_SYNC", "records": batch_data})
        except Exception as e:
            print(f"[!] PostgreSQL sync skipped ({e}). Mining standalone truth anchor.")
            self.mine_block({"type": "STANDALONE_TRUTH_ANCHOR", "status": "Verified"})

if __name__ == "__main__":
    ledger = TruthMandateBlockchain(difficulty=2)
    ledger.sync_from_postgres()
    
    # Save chain to disk for persistence
    with open("truth_mandate_chain.json", "w") as f:
        json.dump(ledger.chain, f, indent=4)
    print("[+] Truth Mandate blockchain state written to truth_mandate_chain.json")

