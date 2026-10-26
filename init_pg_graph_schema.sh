#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${PGDATABASE:-civic_advocate}"
DB_USER="${PGUSER:-postgres}"

echo "=================================================="
echo "Initializing Graph Schema in PostgreSQL ($DB_NAME)"
echo "=================================================="

psql -d "$DB_NAME" -U "$DB_USER" << 'SQL'
-- Enable uuid extension if not present
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Core Nodes (Tables)
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    model VARCHAR(255),
    system_prompt TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS thoughts (
    id VARCHAR(255) PRIMARY KEY,
    agent_id VARCHAR(255) REFERENCES agents(id) ON DELETE CASCADE,
    step INT NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memories (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(50) CHECK (type IN ('episodic', 'semantic')),
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- Requires pgvector extension if using vectors, else omit or use jsonb
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS concepts (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(255),
    description TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    id VARCHAR(255) PRIMARY KEY,
    text TEXT NOT NULL,
    index INT NOT NULL,
    embedding VECTOR(1536)
);

CREATE TABLE IF NOT EXISTS tools (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parameters JSONB
);

-- 2. Relationships (Edge Tables)
CREATE TABLE IF NOT EXISTS thought_next (
    thought_id VARCHAR(255) REFERENCES thoughts(id) ON DELETE CASCADE,
    next_thought_id VARCHAR(255) REFERENCES thoughts(id) ON DELETE CASCADE,
    PRIMARY KEY (thought_id, next_thought_id)
);

CREATE TABLE IF NOT EXISTS thought_references_memory (
    thought_id VARCHAR(255) REFERENCES thoughts(id) ON DELETE CASCADE,
    memory_id VARCHAR(255) REFERENCES memories(id) ON DELETE CASCADE,
    PRIMARY KEY (thought_id, memory_id)
);

CREATE TABLE IF NOT EXISTS memory_mentions_concept (
    memory_id VARCHAR(255) REFERENCES memories(id) ON DELETE CASCADE,
    concept_id VARCHAR(255) REFERENCES concepts(id) ON DELETE CASCADE,
    PRIMARY KEY (memory_id, concept_id)
);

CREATE TABLE IF NOT EXISTS thought_retrieved_chunk (
    thought_id VARCHAR(255) REFERENCES thoughts(id) ON DELETE CASCADE,
    chunk_id VARCHAR(255) REFERENCES chunks(id) ON DELETE CASCADE,
    PRIMARY KEY (thought_id, chunk_id)
);

CREATE TABLE IF NOT EXISTS thought_uses_tool (
    thought_id VARCHAR(255) REFERENCES thoughts(id) ON DELETE CASCADE,
    tool_id VARCHAR(255) REFERENCES tools(id) ON DELETE CASCADE,
    PRIMARY KEY (thought_id, tool_id)
);

-- 3. Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_thoughts_agent ON thoughts(agent_id);
CREATE INDEX IF NOT EXISTS idx_chunks_text_gin ON chunks USING gin(to_tsvector('english', text));
CREATE INDEX IF NOT EXISTS idx_concepts_name_gin ON concepts USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
SQL

echo "PostgreSQL graph schema initialized successfully."
