# #  to monitor for forensic integrity
AUDIT_LOG_DIR = "./forensic_audit_ledgers"
BASELINE_FILE = "truth_mandate_baseline.json"

def get_timestamp():
    return datetime.datetime.now().isoformat()

def compute_sha512(file_path):
    """Generates an immutable SHA-512 fingerprint for forensic data nodes."""
    sha512 = hashlib.sha512()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha512.update(chunk)
    return sha512.hexdigest()

def initialize_forensic_node():
    """Initializes the baseline forensic state for advocacy records."""
    if not os.path.exists(AUDIT_LOG_DIR):
        os.makedirs(AUDIT_LOG_DIR)
        
    baseline = {"timestamp": get_timestamp(), "nodes": {}}
    
    for root, _, files in os.walk(AUDIT_LOG_DIR):
        for name in files:
            path = os.path.join(root, name)
            baseline["nodes"][path] = compute_sha512(path)
            
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=4)
    print(f"Truth Mandate baseline established at {BASELINE_FILE}")

def verify_forensic_integrity():
    """Validates data nodes against the master baseline to ensure immutability."""
    if not os.path.exists(BASELINE_FILE):
        print("Error: No baseline found. Initialize first.")
        return

    with open(BASELINE_FILE, "r") as f:
        baseline = json.load(f)

    for path, original_hash in baseline["nodes"].items():
        if not os.path.exists(path):
            print(f"ALERT: Node missing: {path}")
            continue
        
        current_hash = compute_sha512(path)
        if current_hash != original_hash:
            print(f"CRITICAL: Integrity breach detected at {path}")
        else:
            print(f"Verified: {path} is immutable.")

# Execute initialization to establish the forensic defense layer
if __name__ == "__main__":
    initialize_forensic_node()	

