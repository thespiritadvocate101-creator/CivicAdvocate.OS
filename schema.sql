-- Schema Initialization for Arbitrum Event Logging
BEGIN;

CREATE TABLE IF NOT EXISTS arbitrum_raw_logs (
    id                BIGSERIAL PRIMARY KEY,
    block_number      BIGINT NOT NULL,
    block_hash        VARCHAR(66) NOT NULL,
    transaction_hash  VARCHAR(66) NOT NULL,
    transaction_index INT NOT NULL,
    log_index         INT NOT NULL,
    address           VARCHAR(42) NOT NULL,
    topic0            VARCHAR(66),
    topic1            VARCHAR(66),
    topic2            VARCHAR(66),
    topic3            VARCHAR(66),
    data              TEXT,
    removed           BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_arbitrum_log_id UNIQUE (block_number, transaction_hash, log_index)
);

CREATE INDEX IF NOT EXISTS idx_raw_logs_block ON arbitrum_raw_logs(block_number DESC);
CREATE INDEX IF NOT EXISTS idx_raw_logs_address ON arbitrum_raw_logs(LOWER(address));
CREATE INDEX IF NOT EXISTS idx_raw_logs_topic0 ON arbitrum_raw_logs(topic0);

COMMIT;

-- Domain Table: ERC-20 Transfers
CREATE TABLE IF NOT EXISTS arbitrum_erc20_transfers (
    id               BIGSERIAL PRIMARY KEY,
    contract_address VARCHAR(42) NOT NULL,
    from_address     VARCHAR(42) NOT NULL,
    to_address       VARCHAR(42) NOT NULL,
    amount           NUMERIC(78, 0) NOT NULL,
    block_number     BIGINT NOT NULL,
    transaction_hash VARCHAR(66) NOT NULL,
    log_index        INT NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_erc20_transfer UNIQUE (transaction_hash, log_index)
);

CREATE INDEX IF NOT EXISTS idx_erc20_from ON arbitrum_erc20_transfers(LOWER(from_address));
CREATE INDEX IF NOT EXISTS idx_erc20_to ON arbitrum_erc20_transfers(LOWER(to_address));
CREATE INDEX IF NOT EXISTS idx_erc20_contract ON arbitrum_erc20_transfers(LOWER(contract_address));
