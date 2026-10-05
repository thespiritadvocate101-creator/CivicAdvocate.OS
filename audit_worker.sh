#!/data/data/com.termux/files/usr/bin/env bash
exec 2>&1

WORKER_SCRIPT="$HOME/CivicAdvocate.OS/pg_task_worker.py"
BACKOFF=2
MAX_BACKOFF=30

# Forward termination signals cleanly to child process
trap 'echo "[$(date)] Shutdown signal received. Stopping worker..."; kill -TERM "$CHILD_PID" 2>/dev/null; wait "$CHILD_PID"; exit 0' SIGINT SIGTERM

echo "[$(date)] Starting CivicAdvocate audit worker process supervisor..."

while true; do
    if [ ! -f "$WORKER_SCRIPT" ]; then
        echo "[$(date)] ERROR: Worker script $WORKER_SCRIPT not found."
        sleep 10
        continue
    fi

    # Run Python worker in background to allow signal trapping
    python3 "$WORKER_SCRIPT" &
    CHILD_PID=$!
    wait "$CHILD_PID"
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo "[$(date)] Worker process completed cleanly. Restarting loop..."
        BACKOFF=2
        sleep 2
    else
        echo "[$(date)] Worker process crashed with exit code $EXIT_CODE. Backoff pause for ${BACKOFF}s..."
        sleep $BACKOFF
        # Double backoff delay up to MAX_BACKOFF ceiling
        BACKOFF=$(( BACKOFF * 2 ))
        if [ $BACKOFF -gt $MAX_BACKOFF ]; then
            BACKOFF=$MAX_BACKOFF
        fi
    fi
done
