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
