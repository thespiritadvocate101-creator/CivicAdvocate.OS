import sqlite3
import hashlib
from datetime import datetime, timezone

file_path = "output_report.pdf"
db_path = "audit_ledger.db"

# 1. Calculate the SHA-512 hash of the PDF
hasher = hashlib.sha512()
with open(file_path, 'rb') as f:
    buf = f.read()
    hasher.update(buf)

file_hash = hasher.hexdigest()
timestamp = datetime.now(timezone.utc).isoformat()

# 2. Anchor into the ledger
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ensure the table exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS report_anchors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        sha512_hash TEXT UNIQUE,
        anchored_at TEXT
    )
''')

try:
    cursor.execute('''
        INSERT INTO report_anchors (filename, sha512_hash, anchored_at)
        VALUES (?, ?, ?)
    ''', (file_path, file_hash, timestamp))
    conn.commit()
    print(f"[✓] Successfully anchored {file_path} into {db_path}")
    print(f"[*] SHA-512: {file_hash}")
    print(f"[*] Timestamp: {timestamp}")
except sqlite3.IntegrityError:
    print("[!] This report hash is already anchored in the ledger.")

conn.close()
