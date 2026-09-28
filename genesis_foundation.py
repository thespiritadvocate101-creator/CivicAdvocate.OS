import sqlite3
import hashlib
import datetime

# The foundational text to embed into the architecture
foundational_text = "In the beginning was the Word, and the Word was with God, and the Word was God."

# Generate SHA-512 hash to lock the record
text_bytes = foundational_text.encode('utf-8')
sha512_hash = hashlib.sha512(text_bytes).hexdigest()
timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

# Connect to the local forensic ledger in Termux
conn = sqlite3.connect('forensic_ledger.db')
cursor = conn.cursor()

# Create the genesis architecture table
cursor.execute('''
CREATE TABLE IF NOT EXISTS genesis_foundation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    foundation_text TEXT NOT NULL,
    sha512_digest TEXT NOT NULL UNIQUE
)
''')

# Insert the embedded text into the core architecture
try:
    cursor.execute('''
    INSERT INTO genesis_foundation (timestamp, foundation_text, sha512_digest)
    VALUES (?, ?, ?)
    ''', (timestamp, foundational_text, sha512_hash))
    conn.commit()
    print(f"Foundation embedded successfully.\nHash Digest: {sha512_hash}")
except sqlite3.IntegrityError:
    print("The foundational record is already embedded and secured in the architecture.")

conn.close()
