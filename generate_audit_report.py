import json, os, subprocess, psycopg2

PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5432")
PG_DB   = os.getenv("PGDATABASE", "civicadvocate")
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASS = os.getenv("PGPASSWORD", "")

try:
    conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS)
    cur = conn.cursor()
    cur.execute("SELECT gathered_data, sha512_digest FROM audit_result_ledger WHERE target_entity = 'Abstract 544' ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    if row:
        gathered_data = row[0]
        if isinstance(gathered_data, str):
            gathered_data = json.loads(gathered_data)
        sha512_digest = row[1]
        variance_report = gathered_data.get('cadastral_variance_report', 'No variance report available.')
    else:
        sha512_digest = "PENDING_EXECUTION"
        variance_report = "Pending final ledger sync."
except Exception as e:
    sha512_digest = "ERROR"
    variance_report = str(e)
finally:
    if 'conn' in locals(): conn.close()

latex_content = f"""\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{geometry}}
\\geometry{{a4paper, margin=1in}}
\\usepackage{{hyperref}}

\\title{{CivicAdvocate.OS \\\\ Cadastral Variance \\& Proximity Audit}}
\\author{{Lead Partner and Architect: Brandon Lynn Campbell}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle

\\section*{{Audit Target}}
\\textbf{{Jurisdiction:}} Johnson County, TX\\\\
\\textbf{{Legal Description:}} The Silas Elbert Bandy Survey, Abstract 544

\\section*{{Cryptographic Integrity}}
\\textbf{{SHA-512 State Digest:}}\\\\
\\texttt{{{sha512_digest}}}

\\section*{{Geospatial Cross-Reference Results}}
\\begin{{verbatim}}
{variance_report}
\\end{{verbatim}}

\\vfill
\\begin{{center}}
\\footnotesize{{Generated automatically by CivicAdvocate.OS Master Pipeline}}
\\end{{center}}
\\end{{document}}
"""

with open('abstract_544_audit_report.tex', 'w') as f:
    f.write(latex_content)

subprocess.run(["pdflatex", "-interaction=batchmode", "abstract_544_audit_report.tex"], capture_output=True)
print("Report compiled successfully.")
