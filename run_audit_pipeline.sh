#!/bin/bash
cd ~/CivicAdvocate.OS

echo "=== [$(date -Iseconds)] Starting opBNB Audit Pipeline ===" >> pipeline_cron.log

# Step 1: Scrape transfers and pipe to PostgreSQL
./opbnb_meganode_pipeline.sh 0x4200000000000000000000000000000000000015 | psql -d civic_audit -q >> pipeline_cron.log 2>&1

# Step 2: Generate SHA-512 seals for unsealed records
python3 seal_opbnb_ledger.py >> pipeline_cron.log 2>&1

# Step 3: Export sealed ledger to W3C JSON-LD
python3 export_opbnb_jsonld.py >> pipeline_cron.log 2>&1

# Step 4: Deploy to GitHub Pages
git add opbnb_ledger.jsonld >> pipeline_cron.log 2>&1

# Only commit and push if the file actually changed
if ! git diff --staged --quiet; then
    git commit -m "Auto-seal audit ledger: $(date -Iseconds)" >> pipeline_cron.log 2>&1
    git push >> pipeline_cron.log 2>&1
    echo "-> Deployed new ledger signatures to GitHub" >> pipeline_cron.log
else
    echo "-> No new transfers. Ledger is current." >> pipeline_cron.log
fi

echo "=== [$(date -Iseconds)] Pipeline Complete ===" >> pipeline_cron.log
echo "" >> pipeline_cron.log
