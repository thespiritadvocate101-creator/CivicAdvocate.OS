#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo "Diagnosing Neo4j Service Status"
echo "=================================================="

# 1. Check if Neo4j process is running
if pgrep -f "neo4j" > /dev/null; then
    echo "[INFO] Neo4j process detected running."
else
    echo "[WARNING] Neo4j process is NOT running."
    
    # 2. Try starting via termux-services (runit) if configured
    if command -v sv &> /dev/null && [ -d "$PREFIX/var/service/neo4j" ]; then
        echo "[INFO] Starting Neo4j via termux-services..."
        sv up neo4j || true
    elif command -v neo4j &> /dev/null; then
        echo "[INFO] Starting Neo4j via CLI..."
        neo4j start || true
    else
        echo "[ERROR] Neo4j executable or service definition not found in standard Termux paths."
        echo "Please check how Neo4j is installed or start it manually."
    fi
fi

# 3. Wait a moment and test connection
echo "Waiting for Neo4j HTTP API to become available..."
for i in {1..10}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:7474/ | grep -q "200\|401"; then
        echo "[SUCCESS] Neo4j is up and responding on port 7474!"
        exit 0
    fi
    sleep 2
done

echo "[ERROR] Neo4j failed to respond on port 7474 after 20 seconds."
exit 1
