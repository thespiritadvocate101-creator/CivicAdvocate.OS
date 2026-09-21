import psycopg2

conn = psycopg2.connect(dbname="postgres", user="u0_a540", host="localhost", port=5432)
cursor = conn.cursor()
cursor.execute("SELECT status, COUNT(*) FROM task_queue GROUP BY status;")
for row in cursor.fetchall():
    print(f"Status: {row[0]} | Count: {row[1]}")
conn.close()
