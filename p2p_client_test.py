#!/usr/bin/env python3
import socket
import json
import hashlib

def test_mesh_connection(host='127.0.0.1', port=8888):
    print(f"[-] Connecting to CivicAdvocate.OS mesh node at {host}:{port}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        data = client_socket.recv(4096)
        response = json.loads(data.decode('utf-8'))
        
        payload = response["payload"]
        received_seal = response["cryptographic_seal"]
        
        # Recompute seal to verify integrity
        payload_string = json.dumps(payload, sort_keys=True)
        computed_seal = hashlib.sha256(payload_string.encode('utf-8')).hexdigest()
        
        print("\n[+] --- INCOMING MESH MANIFEST ---")
        print(json.dumps(payload, indent=2))
        print(f"[+] Received Seal: {received_seal}")
        
        if received_seal == computed_seal:
            print("[+] INTEGRITY VERIFIED: Cryptographic seal matches absolute truth lock.")
        else:
            print("[!] INTEGRITY WARNING: Seal mismatch detected!")

if __name__ == "__main__":
    test_mesh_connection()
