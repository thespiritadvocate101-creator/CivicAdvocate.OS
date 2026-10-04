#!/bin/bash
cd ~/CivicAdvocate.OS
if ! pgrep -f "pg_task_worker.py" > /dev/null; then
    echo "[$(date)] Worker daemon inactive. Initiating recovery..." >> pipeline_watch.log
    nohup env PGDATABASE=civicadvocate PGUSER=postgres PYTHONUNBUFFERED=1 python3 pg_task_worker.py > worker.log 2>&1 &
fi
