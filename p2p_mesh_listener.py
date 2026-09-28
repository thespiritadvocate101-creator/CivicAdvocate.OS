#!/usr/bin/env python3
import socket
import hashlib
import json
from datetime import datetime, timezone

def start_mesh_node(host='0.0.0.0', port=8888):
    print(f"[-] Initializing CivicAdvocate.OS P2P Mesh Listener on {host}:{port}...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("[+] Mesh node active. Broadcasting absolute truth across the network...")
    
    while True:
        conn, addr = server_socket.accept()
        print(f"[+] Peer connection established from {addr}")
        try:
            manifest_data = {
                "node": "CivicAdvocate.OS Master",
                "cadastral_anchor": "Abstract 544 - Silas Elbert Bandy Survey",
                "status": "ABSOLUTE_TRUTH_LOCKED",
                "timestamp_utc": datetime.now(timezone.utc).isoformat()
            }
            payload = json.dumps(manifest_data, sort_keys=True)
            seal = hashlib.sha256(payload.encode('utf-8')).hexdigest()
            response = {"payload": manifest_data, "cryptographic_seal": seal}
            conn.sendall(json.dumps(response, indent=2).encode('utf-8'))
        except Exception as e:
            print(f"[!] Transmission error: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    start_mesh_node()
