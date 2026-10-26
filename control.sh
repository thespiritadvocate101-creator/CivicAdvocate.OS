#!/usr/bin/env bash
PID_FILE="server.pid"
LOG_FILE="server.log"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Server is already running (PID: $(cat "$PID_FILE"))."
            exit 1
        fi
        echo "Starting secure API server..."
        nohup ./server.sh > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "Server started with PID $(cat "$PID_FILE")."
        ;;
    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "No PID file found. Is the server running?"
            exit 1
        fi
        PID=$(cat "$PID_FILE")
        echo "Stopping server (PID: $PID)..."
        kill "$PID" 2>/dev/null
        rm -f "$PID_FILE"
        echo "Server stopped."
        ;;
    logs)
        tail -n 50 -f "$LOG_FILE"
        ;;
    *)
        echo "Usage: $0 {start|stop|logs}"
        exit 1
        ;;
esac
