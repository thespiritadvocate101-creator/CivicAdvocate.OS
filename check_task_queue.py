import psycopg2

try:
    conn = psycopg2.connect(dbname="postgres", user="u0_a540", host="localhost", port=5432)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM task_queue;")
    rows = cursor.fetchall()
    if not rows:
        print("Task queue is currently empty.")
    for row in rows:
        print(row)
    conn.close()
except Exception as e:
    print(f"Database error: {e}")
