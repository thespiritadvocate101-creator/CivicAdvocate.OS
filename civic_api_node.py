from flask import Flask, jsonify, request
import sqlite3
import psycopg2
import json

app = Flask(__name__)

@app.route('/genesis', methods=['GET'])
def get_genesis():
    try:
        conn = sqlite3.connect('forensic_ledger.db')
        cursor = conn.cursor()
        cursor.execute("SELECT sha512_digest FROM genesis_foundation ORDER BY id ASC LIMIT 1;")
        result = cursor.fetchone()
        conn.close()

        if result:
            return jsonify({
                "foundation_status": "Active",
                "sha512_digest": result[0]
            }), 200
        else:
            return jsonify({"error": "Genesis block missing"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cadastral/anchors', methods=['GET'])
def get_cadastral_anchors():
    try:
        conn = sqlite3.connect('forensic_ledger.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, target_abstract, report_payload, sha512_digest, created_at FROM audit_anchors;")
        rows = cursor.fetchall()
        conn.close()

        anchors = []
        for row in rows:
            anchors.append({
                "id": row[0],
                "target_abstract": row[1],
                "report_payload": json.loads(row[2]) if row[2] else None,
                "sha512_digest": row[3],
                "created_at": row[4]
            })

        return jsonify({
            "status": "success",
            "target_domain": "Abstract 544 Cryptographic Anchors",
            "anchors": anchors
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/cadastral/records', methods=['GET', 'POST'])
def handle_cadastral_records():
    if request.method == 'POST':
        try:
            req_data = request.get_json(silent=True) or {}
            status = req_data.get('status', 'PENDING')
            task_payload = req_data.get('task_payload', req_data)

            conn = psycopg2.connect(dbname='postgres')
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO task_queue (status, task_payload, created_at) VALUES (%s, %s::jsonb, NOW()) RETURNING id, status, created_at;",
                (status, json.dumps(task_payload))
            )
            new_row = cur.fetchone()
            conn.commit()
            conn.close()

            return jsonify({
                "status": "success",
                "message": "Audit task enqueued successfully",
                "record": {
                    "id": new_row[0],
                    "status": new_row[1],
                    "created_at": new_row[2].isoformat() if new_row[2] else None,
                    "task_payload": task_payload
                }
            }), 201
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        try:
            conn = psycopg2.connect(dbname='postgres')
            cur = conn.cursor()
            cur.execute("SELECT * FROM task_queue;")
            colnames = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            conn.close()

            records = []
            for row in rows:
                record = {}
                for i, val in enumerate(row):
                    if hasattr(val, 'isoformat'):
                        record[colnames[i]] = val.isoformat()
                    else:
                        record[colnames[i]] = val
                records.append(record)

            return jsonify({
                "status": "success",
                "target_abstract": "Abstract 544",
                "senior_patent": "Silas Elbert Bandy",
                "records": records
            }), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("CivicAdvocate.OS API Node starting...")
    print("Broadcasting foundation on http://0.0.0.0:8086")
    app.run(host='0.0.0.0', port=8086)
