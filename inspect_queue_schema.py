import psycopg2

try:
    conn = psycopg2.connect(dbname="postgres", user="u0_a540", host="localhost", port=5432)
    cursor = conn.cursor()
    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'task_queue';")
    for row in cursor.fetchall():
        print(row)
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
