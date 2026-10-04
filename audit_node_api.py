import json, os, psycopg2, getpass
from flask import Flask, jsonify, send_file

app = Flask(__name__)

def get_db_connection():
    # Omitting host/port forces psycopg2 to use the local Unix socket
    # Defaulting to the current Termux user
    db_user = os.getenv("PGUSER", getpass.getuser())
    return psycopg2.connect(
        dbname=os.getenv("PGDATABASE", "civicadvocate"),
        user=db_user
    )

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "node": "CivicAdvocate.OS Johnson County",
        "status": "secure",
        "endpoints": {
            "ledger_feed": "/api/v1/ledger",
            "master_pdf_report": "/api/v1/reports/latest"
        }
    })

@app.route("/api/v1/ledger", methods=["GET"])
def get_ledger():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, source_task_id, target_entity, sha512_digest FROM audit_result_ledger ORDER BY id DESC LIMIT 50;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        ledger = [{
            "id": r[0],
            "source_task_id": r[1],
            "target_entity": r[2],
            "sha512_digest": r[3]
        } for r in rows]
        return jsonify({"status": "secure", "node": "CivicAdvocate.OS Johnson County", "ledger_entries": ledger})
    except Exception as e:
        return jsonify({"status": "error", "error_message": str(e)}), 500

@app.route("/api/v1/reports/latest", methods=["GET"])
def get_latest_report():
    report_path = "multi_abstract_audit_report.pdf"
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True)
    return jsonify({"error": "Master audit report not compiled yet."}), 404

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8090, debug=False)
