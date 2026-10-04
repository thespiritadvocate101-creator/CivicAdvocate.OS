import json
import sys
import hashlib

def verify_chain_integrity(ledger_filepath: str, required_chain_id: int) -> bool:
    """
    Validates line-by-line block linkage and strictly enforces a Chain ID match 
    on each JSON object in a JSONL stream.
    """
    print(f"[*] Starting strict audit for Chain ID: {required_chain_id}")
    print(f"[*] Target file: {ledger_filepath}")
    
    blocks = []
    try:
        with open(ledger_filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    blocks.append(json.loads(clean_line))
                except json.JSONDecodeError:
                    print(f"[-] Error: Defective serialization at line {line_num}.")
                    return False
    except FileNotFoundError:
        print(f"[-] Error: Target ledger file not found at '{ledger_filepath}'")
        return False

    if not blocks:
        print("[-] Error: Stream container is empty.")
        return False

    for i, block in enumerate(blocks):
        # 1. Enforce specific Chain ID alignment
        block_chain_id = block.get("chain_id")
        if block_chain_id != required_chain_id:
            print(f"🚨 CRITICAL: Chain ID mismatch at Block {i}!")
            print(f"Expected: {required_chain_id} | Found: {block_chain_id}")
            return False
            
        # 2. Sequential cryptographic linkage validation
        if i > 0:
            previous_block = blocks[i - 1]
            actual_prev_hash = block.get("previous_hash")
            
            # Re-verify the absolute SHA-512 state of the previous block
            serialized_prev = json.dumps(previous_block, sort_keys=True).encode('utf-8')
            computed_prev_hash = hashlib.sha512(serialized_prev).hexdigest()
            
            if actual_prev_hash != computed_prev_hash:
                print(f"🚨 BREACH DETECTED: Tampering found at Block link {i}")
                return False
                
    print("✅ Chain identification and link validation 100% secure.")
    return True

if __name__ == "__main__":
    # Point directly to your active repository path
    success = verify_chain_integrity("ledger/mission_ledger.jsonl", required_chain_id=101)
    sys.exit(0 if success else 1)

