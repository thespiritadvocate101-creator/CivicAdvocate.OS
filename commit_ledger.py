import subprocess
import json
import hashlib
from datetime import datetime, timezone

IDENTITY_KEY = "Campbell; Bandy (Lynn) absolute"
LOG_FILE = "deep_forensic_audit.log"

def run_cmd(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Command failed: {' '.join(args)}\nError: {result.stderr}")
    return result.stdout.strip()

def secure_git_commit():
    print(f"[*] INITIATING CRITICAL REPOSITORY VERSION LOCK")
    
    try:
        # 1. Stage all active core assets
        run_cmd(["git", "add", "core_orchestrator.sh", "run_audit_loop.sh"])
        run_cmd(["git", "add", "*.py", "reconciliation_manifest.json"])
        run_cmd(["git", "add", "archive_store/"])
        run_cmd(["git", "add", LOG_FILE])
        
        # 2. Generate a snapshot checksum of the current log state for the commit message
        with open(LOG_FILE, "rb") as f:
            log_bytes = f.read()
            log_sha = hashlib.sha512(log_bytes).hexdigest()
            
        timestamp_str = datetime.now(timezone.utc).isoformat()
        commit_msg = f"[LEDGER_COMMIT] | TIMESTAMP: {timestamp_str} | LOG_SHA: {log_sha[:16]}... | ARCHITECT: {IDENTITY_KEY}"
        
        # 3. Execute the signed commit string
        commit_output = run_cmd(["git", "commit", "-m", commit_msg])
        
        print("------------------------------------------------------------------------")
        print(f"[✓] REPOSITORY SEALS LOCKED SUCCESSFULLY")
        print(f"[✓] COMMIT HASHESTEAD: \n{commit_output}")
        print("------------------------------------------------------------------------")
        
    except Exception as e:
        print(f"[!] COMMIT INTERRUPTION: {str(e)}")

if __name__ == "__main__":
    secure_git_commit()
