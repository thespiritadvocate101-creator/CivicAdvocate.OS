#!/usr/bin/env bash

DB_NAME="civicadvocate_db"
ERC20_TRANSFER_TOPIC="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
BATCH_SIZE=100
POLL_INTERVAL=5

LAST_ID=0

echo "==> [CivicAdvocate.OS] Starting ERC-20 Bash Decoder Daemon..."

# Helper: Convert 32-byte topic hex to 20-byte EVM address
topic_to_address() {
    local topic="$1"
    topic="${topic#0x}"
    if [ ${#topic} -ge 40 ]; then
        echo "0x${topic: -40}" | tr '[:upper:]' '[:lower:]'
    else
        echo "0x0000000000000000000000000000000000000000"
    fi
}

# Helper: Convert 32-byte hex data to decimal uint256
hex_to_uint256() {
    local hex_data="$1"
    hex_data="${hex_data#0x}"
    if [ -z "$hex_data" ]; then
        echo "0"
        return
    fi
    # Slice first 32 bytes (64 hex characters) and force uppercase for bc
    local clean_hex="${hex_data:0:64}"
    clean_hex=$(echo "$clean_hex" | tr '[:lower:]' '[:upper:]')
    echo "ibase=16; $clean_hex" | bc 2>/dev/null || echo "0"
}

while true; do
    # Fetch batch of raw logs matching ERC-20 Transfer topic0
    QUERY="SELECT id, block_number, transaction_hash, log_index, LOWER(address), topic1, topic2, COALESCE(data, '0x0') 
           FROM arbitrum_raw_logs 
           WHERE topic0 = '$ERC20_TRANSFER_TOPIC' AND id > $LAST_ID 
           ORDER BY id ASC 
           LIMIT $BATCH_SIZE;"

    RAW_DATA=$(psql -d "$DB_NAME" -t -A -F "|" -c "$QUERY" 2>/dev/null)

    if [ -z "$RAW_DATA" ]; then
        sleep "$POLL_INTERVAL"
        continue
    fi

    VALUES_LIST=""
    COUNT=0

    # Process each row piped from psql
    while IFS="|" read -r id block_number tx_hash log_index contract_address topic1 topic2 data; do
        LAST_ID="$id"

        # Skip invalid logs missing indexed topics
        if [ -z "$topic1" ] || [ -z "$topic2" ]; then
            continue
        fi

        FROM_ADDR=$(topic_to_address "$topic1")
        TO_ADDR=$(topic_to_address "$topic2")
        AMOUNT=$(hex_to_uint256 "$data")

        if [ $COUNT -gt 0 ]; then
            VALUES_LIST+=", "
        fi

        VALUES_LIST+="('$contract_address', '$FROM_ADDR', '$TO_ADDR', $AMOUNT, $block_number, '$tx_hash', $log_index)"
        COUNT=$((COUNT + 1))
    done <<< "$RAW_DATA"

    # Execute bulk insert into normalized domain table
    if [ $COUNT -gt 0 ]; then
        INSERT_SQL="INSERT INTO arbitrum_erc20_transfers (contract_address, from_address, to_address, amount, block_number, transaction_hash, log_index) 
                    VALUES $VALUES_LIST 
                    ON CONFLICT (transaction_hash, log_index) DO NOTHING;"

        psql -d "$DB_NAME" -c "$INSERT_SQL" > /dev/null 2>&1
        echo "[+] Decoded and inserted $COUNT transfers up to raw log ID $LAST_ID"
    fi
done
