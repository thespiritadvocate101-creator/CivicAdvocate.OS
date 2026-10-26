import urllib.request
import json
import base64
import os

url = os.environ.get("NEO4J_HTTP_URL", "http://localhost:7474/db/neo4j/tx/commit")
user = os.environ.get("NEO4J_USER", "neo4j")
password = os.environ.get("NEO4J_PASSWORD", "password")

statements = [
    "CREATE CONSTRAINT agent_id_unique IF NOT EXISTS FOR (n:Agent) REQUIRE n.id IS UNIQUE;",
    "CREATE CONSTRAINT thought_id_unique IF NOT EXISTS FOR (n:Thought) REQUIRE n.id IS UNIQUE;",
    "CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (n:Memory) REQUIRE n.id IS UNIQUE;",
    "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (n:Concept) REQUIRE n.id IS UNIQUE;",
    "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (n:Chunk) REQUIRE n.id IS UNIQUE;",
    "CREATE CONSTRAINT tool_id_unique IF NOT EXISTS FOR (n:Tool) REQUIRE n.id IS UNIQUE;",
    "CREATE VECTOR INDEX memory_embedding_idx IF NOT EXISTS FOR (n:Memory) ON (n.embedding) OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' }};",
    "CREATE VECTOR INDEX chunk_embedding_idx IF NOT EXISTS FOR (n:Chunk) ON (n.embedding) OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' }};",
    "CREATE FULLTEXT INDEX chunk_text_idx IF NOT EXISTS FOR (n:Chunk) ON EACH [n.text];",
    "CREATE FULLTEXT INDEX concept_text_idx IF NOT EXISTS FOR (n:Concept) ON EACH [n.name, n.description];"
]

payload = {"statements": [{"statement": s} for s in statements]}
data = json.dumps(payload).encode("utf-8")

req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
auth_str = f"{user}:{password}"
base64_auth = base64.b64encode(auth_str.encode("ascii")).decode("ascii")
req.add_header("Authorization", f"Basic {base64_auth}")

try:
    with urllib.request.urlopen(req) as response:
        res_body = json.loads(response.read().decode("utf-8"))
        if res_body.get("errors"):
            print("Errors returned from Neo4j:", res_body["errors"])
        else:
            print("Successfully initialized all schema constraints and indexes!")
except Exception as e:
    print(f"Failed to connect or execute against Neo4j HTTP API: {e}")
