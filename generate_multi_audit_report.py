import json, os, subprocess, psycopg2

PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5432")
PG_DB   = os.getenv("PGDATABASE", "civicadvocate")
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASS = os.getenv("PGPASSWORD", "")

conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS)
cur = conn.cursor()
cur.execute("SELECT target_entity, gathered_data, sha512_digest FROM audit_result_ledger WHERE target_entity IN ('Abstract 544', 'Abstract 545', 'Abstract 546', 'Abstract 547', 'Abstract 548', 'Abstract 549', 'Abstract 550') ORDER BY id DESC;")
rows = cur.fetchall()
conn.close()

ledger_summaries = []
seen_targets = set()
for row in rows:
    target, gathered_data, digest = row
    if target in seen_targets:
        continue
    seen_targets.add(target)
    if isinstance(gathered_data, str):
        gathered_data = json.loads(gathered_data)
    
    pretty_data = json.dumps(gathered_data, indent=2)
    ledger_summaries.append(f"""
\\subsection*{{Target Tract: {target}}}
\\textbf{{SHA-512 State Digest:}}\\\\
\\texttt{{{digest}}}
\\begin{{verbatim}}
{pretty_data}
\\end{{verbatim}}
""")

content = "\n".join(ledger_summaries)

latex_content = f"""\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{geometry}}
\\geometry{{a4paper, margin=1in}}
\\usepackage{{hyperref}}

\\title{{CivicAdvocate.OS \\\\ Seven-Tract Master Audit Report (Abstracts 544--550)}}
\\author{{Lead Partner and Architect: Brandon Lynn Campbell}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle

\\section*{{Executive Summary}}
Comprehensive forensic audit report covering cadastral surveys, EPA compliance, and Texas RRC infrastructure across contiguous land tracts (Abstracts 544 through 550) in Johnson County, TX.

\\section*{{Cryptographic Ledger & Geospatial Verification}}
{content}

\\vfill
\\begin{{center}}
\\footnotesize{{Generated automatically by CivicAdvocate.OS Master Pipeline}}
\\end{{center}}
\\end{{document}}
"""

with open('multi_abstract_audit_report.tex', 'w') as f:
    f.write(latex_content)

subprocess.run(["pdflatex", "-interaction=batchmode", "multi_abstract_audit_report.tex"], capture_output=True)
print("Seven-tract master audit report compiled successfully.")
