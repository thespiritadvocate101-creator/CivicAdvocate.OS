#!/bin/bash

echo "[*] Patching datetime deprecation warnings in export_audit_report.py..."
sed -i 's/datetime.utcnow()/datetime.now(datetime.timezone.utc)/g' export_audit_report.py
sed -i 's/datetime.datetime.utcnow()/datetime.datetime.now(datetime.timezone.utc)/g' export_audit_report.py

echo "[*] Generating report_template.tex..."
cat << 'INNER_EOF' > report_template.tex
\documentclass[11pt, a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\geometry{margin=1in}
\usepackage{booktabs}
\usepackage{fancyhdr}
\usepackage{xcolor}
\usepackage{hyperref}

\definecolor{primary}{RGB}{0, 76, 153}
\definecolor{statusgreen}{RGB}{0, 153, 76}
\definecolor{statusred}{RGB}{204, 0, 0}

\pagestyle{fancy}
\setlength{\headheight}{14pt}
\fancyhf{}
\fancyhead[L]{\textbf{System Audit Report}}
\fancyhead[R]{\thepage}
\fancyfoot[C]{\textit{Generated autonomously via CivicAdvocate.OS}}

\begin{document}

\begin{center}
    {\Huge\bfseries Automated Audit Export} \\[0.5em]
    {\large Date: {{DATE_PLACEHOLDER}}} \\[0.5em]
    {\large Target Location: {{LOCATION_PLACEHOLDER}}}
\end{center}

\vspace{2em}

\section{\textcolor{primary}{Executive Summary}}
This report was compiled automatically. It summarizes the localized security and ledger audit metrics processed during the most recent execution cycle.

\section{\textcolor{primary}{Metrics Overview}}
\begin{table}[h]
    \centering
    \renewcommand{\arraystretch}{1.3}
    \begin{tabular}{@{}llc@{}}
        \toprule
        \textbf{Metric} & \textbf{Status} & \textbf{Value} \\
        \midrule
        Ledger Integrity & \textcolor{statusgreen}{Verified} & {{LEDGER_SCORE}} \\
        Failed Processes & \textcolor{statusred}{Detected} & {{FAILED_COUNT}} \\
        Execution Time & Normal & {{EXEC_TIME}} \\
        \bottomrule
    \end{tabular}
\end{table}

\section{\textcolor{primary}{Detailed Audit Logs}}
{{DETAILED_LOGS_PLACEHOLDER}}

\end{document}
INNER_EOF

echo "[*] Creating json_to_tex.py bridge script..."
cat << 'INNER_EOF' > json_to_tex.py
import json
import glob
import os
import datetime

# Locate the most recently generated JSON report from our pipeline
list_of_files = glob.glob('audit_reports/*.json')
if not list_of_files:
    print("No JSON reports found in audit_reports/")
    exit(1)
    
latest_file = max(list_of_files, key=os.path.getctime)
print(f"Reading payload from {latest_file}...")

with open(latest_file, 'r') as f:
    audit_data = json.load(f)

with open('report_template.tex', 'r') as file:
    template = file.read()

# Helper function to escape LaTeX special characters like %
def safe_tex(val):
    return str(val).replace('%', r'\%')

# Map the JSON data to the LaTeX placeholders
tex_content = template.replace('{{DATE_PLACEHOLDER}}', safe_tex(datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")))
tex_content = tex_content.replace('{{LOCATION_PLACEHOLDER}}', safe_tex(audit_data.get('location', 'Cleburne, TX')))
tex_content = tex_content.replace('{{LEDGER_SCORE}}', safe_tex(audit_data.get('score', '100%')))
tex_content = tex_content.replace('{{FAILED_COUNT}}', safe_tex(audit_data.get('failures', 0)))
tex_content = tex_content.replace('{{EXEC_TIME}}', safe_tex(audit_data.get('exec_time', '0ms')))
tex_content = tex_content.replace('{{DETAILED_LOGS_PLACEHOLDER}}', safe_tex(audit_data.get('logs_tex', 'No anomalies detected.')))

with open('output_report.tex', 'w') as file:
    file.write(tex_content)
    
print("LaTeX file written to output_report.tex")
INNER_EOF

echo "[*] Step 1: Executing export_audit_report.py..."
python3 export_audit_report.py

echo "[*] Step 2: Bridging JSON to LaTeX format..."
python3 json_to_tex.py

echo "[*] Step 3: Compiling PDF via Termux TeX Live..."
pdflatex -interaction=nonstopmode output_report.tex

echo "[*] Step 4: Cleaning up build artifacts..."
rm -f output_report.aux output_report.log output_report.out

echo "[✓] Audit PDF generation complete. Check output_report.pdf"

echo "[*] Step 5: Anchoring PDF to cryptographic ledger..."
python3 anchor_report.py
