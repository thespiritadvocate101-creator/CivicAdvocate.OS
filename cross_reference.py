#!/usr/bin/env python3
import sqlite3
import re
from difflib import SequenceMatcher

DB_NAME = "audit_ledger.db"
SIMILARITY_THRESHOLD = 0.75

def normalize_entity_name(name: str) -> str:
    if not name:
        return ""
    name = name.upper()
    name = re.sub(r'[^\w\s]', '', name)
    suffixes = {'INC', 'LLC', 'CORP', 'CORPORATION', 'CO', 'LIMITED', 'LTD', 'SERVICES', 'COMPANY', 'GROUP'}
    tokens = [token for token in name.split() if token not in suffixes]
    return " ".join(tokens)

def init_matches_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cross_reference_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        federal_entity TEXT NOT NULL,
        state_entity TEXT NOT NULL,
        similarity_score REAL NOT NULL,
        match_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(federal_entity, state_entity)
    );
    """)
    conn.commit()

def cross_reference_ledger():
    conn = sqlite3.connect(DB_NAME)
    init_matches_table(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT recipient_name FROM normalized_federal_awards WHERE recipient_name IS NOT NULL AND recipient_name != '';")
    fed_entities = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT vendor_name FROM normalized_state_expenditures WHERE vendor_name IS NOT NULL AND vendor_name != '';")
    state_entities = [row[0] for row in cursor.fetchall()]

    print(f"[*] Scanning {len(fed_entities)} Federal Recipient(s) against {len(state_entities)} State Vendor(s)...\n")

    matches = []
    for fed_raw in fed_entities:
        fed_clean = normalize_entity_name(fed_raw)
        if not fed_clean:
            continue

        for state_raw in state_entities:
            state_clean = normalize_entity_name(state_raw)
            if not state_clean:
                continue

            if fed_clean == state_clean:
                matches.append((fed_raw, state_raw, 1.00, "EXACT_NORMALIZED"))
            else:
                ratio = SequenceMatcher(None, fed_clean, state_clean).ratio()
                if ratio >= SIMILARITY_THRESHOLD:
                    matches.append((fed_raw, state_raw, round(ratio, 2), "FUZZY_MATCH"))

    if matches:
        cursor.executemany("""
            INSERT INTO cross_reference_matches (federal_entity, state_entity, similarity_score, match_type)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(federal_entity, state_entity) DO UPDATE SET
                similarity_score=excluded.similarity_score,
                match_type=excluded.match_type,
                created_at=CURRENT_TIMESTAMP;
        """, matches)
        conn.commit()

        print(f"[+] Indexed {len(matches)} match(es) into 'cross_reference_matches'.\n")
        header = f"{'FEDERAL RECIPIENT':<40} | {'STATE VENDOR':<40} | {'SCORE':<5} | {'MATCH TYPE'}"
        print(header)
        print("-" * len(header))
        for fed, state, score, m_type in matches:
            print(f"{fed[:38]:<40} | {state[:38]:<40} | {score:<5.2f} | {m_type}")
    else:
        print("[-] No entity overlaps found matching or exceeding the similarity threshold.")

    conn.close()

if __name__ == "__main__":
    cross_reference_ledger()
