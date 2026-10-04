#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

echo "=== CivicAdvocate.OS Maintenance Routine ==="

# 1. Clear package manager cache and temporary files safely
pkg clean 2>/dev/null || true
find /data/data/com.termux/files/usr/tmp -mindepth 1 -delete 2>/dev/null || true
rm -rf ~/.cache/* 2>/dev/null || true

# 2. Force PostgreSQL checkpoint to flush and recycle old WAL segments
if pg_isready -q; then
    echo "[+] Requesting PostgreSQL checkpoint to clear WAL logs..."
    psql -d civicadvocate -c "CHECKPOINT;" >/dev/null
    echo "[+] Checkpoint complete. Inactive WAL logs recycled."
else
    echo "[!] PostgreSQL is not running. Skipping checkpoint."
fi

# 3. Truncate operational logs over 10MB
find ~/CivicAdvocate.OS -name "*.log" -size +10M -exec truncate -s 0 {} + 2>/dev/null || true

# 4. Display active storage allocation
df -h /data/data/com.termux/files | awk 'NR==1 || NR==2'
