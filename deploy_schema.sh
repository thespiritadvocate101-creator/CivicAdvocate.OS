#!/usr/bin/env zsh

DB_NAME="civicadvocate_db"
SCHEMA_FILE="schema.sql"
PG_SOCKET_DIR="$PREFIX/var/lib/postgresql"

echo "==> [CivicAdvocate.OS] Starting Database Deployment..."

if ! pg_isready -q; then
    echo "[-] PostgreSQL server is not running. Attempting startup..."
    if [ -d "$PG_SOCKET_DIR" ]; then
        pg_ctl -D "$PG_SOCKET_DIR" -l "$PREFIX/var/log/postgres.log" start
        sleep 2
    else
        echo "[!] Error: PostgreSQL data directory $PG_SOCKET_DIR not found."
        exit 1
    fi
fi

if ! pg_isready -q; then
    echo "[!] Error: Failed to start PostgreSQL server."
    exit 1
fi
echo "[+] PostgreSQL server is online."

DB_EXISTS=$(psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" postgres 2>/dev/null)

if [ "$DB_EXISTS" = "1" ]; then
    echo "[+] Database '$DB_NAME' already exists."
else
    echo "[-] Database '$DB_NAME' not found. Creating..."
    createdb "$DB_NAME"
fi

if [ ! -f "$SCHEMA_FILE" ]; then
    echo "[!] Error: Schema file '$SCHEMA_FILE' not found in current directory."
    exit 1
fi

echo "==> Executing '$SCHEMA_FILE' against '$DB_NAME'..."
psql -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$SCHEMA_FILE"
