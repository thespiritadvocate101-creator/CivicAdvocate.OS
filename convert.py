import json
import csv
import os

# Define the file paths
jsonl_file_path = '/data/data/com.termux/files/usr/var/lib/truth_mandate/ledger/mission_ledger.jsonl'
csv_file_path = '/data/data/com.termux/files/usr/var/lib/truth_mandate/ledger/mission_ledger.csv'

# Ensure the output directory exists
os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)

try:
    # First pass: Scan all rows to collect all possible keys/headers
    headers = set()
    with open(jsonl_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    headers.update(data.keys())
                except json.JSONDecodeError:
                    continue
    
    headers = sorted(list(headers))

    # Second pass: Write data to CSV
    with open(jsonl_file_path, 'r', encoding='utf-8') as infile, \
         open(csv_file_path, 'w', newline='', encoding='utf-8') as outfile:
        
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()
        
        for line in infile:
            if line.strip():
                try:
                    data = json.loads(line)
                    # Convert list or dict values to strings to prevent messy cells
                    for key, value in data.items():
                        if isinstance(value, (dict, list)):
                            data[key] = json.dumps(value)
                    writer.writerow(data)
                except json.JSONDecodeError:
                    print(f"Skipping malformed JSON line: {line.strip()}")
                    
    print(f"Successfully converted to CSV! File saved at:\n{csv_file_path}")

except FileNotFoundError:
    print(f"Error: The file at {jsonl_file_path} was not found. Please verify the path.")

