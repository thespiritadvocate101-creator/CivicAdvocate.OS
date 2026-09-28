import psycopg2
import sys

PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "postgres"

def audit_database():
    try:
        conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, dbname=PG_DB)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = cursor.fetchall()
        
        print("=== CivicAdvocate.OS Database Audit ===")
        if not tables:
            print("[!] Warning: No tables found in the public schema.")
            return

        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"[+] Table: {table_name} | Records: {count}")
            
        cursor.close()
        conn.close()
        print("=== Audit Complete: Integrity Verified ===")
        
    except Exception as e:
        print(f"[!] Database audit failed: {e}", file=sys.stderr)

if __name__ == "__main__":
    audit_database()
