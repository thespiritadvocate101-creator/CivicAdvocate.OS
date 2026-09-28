#!/usr/bin/env python3
import subprocess
import json
import os

def pin_manifest_to_ipfs():
    target_file = "earmark_routing_manifest.json"
    
    if not os.path.exists(target_file):
        print(f"[!] Error: {target_file} not found in current directory.")
        return

    print(f"[-] Initializing IPFS pin sequence for {target_file}...")
    try:
        # Execute local IPFS CLI add command
        result = subprocess.run(
            ["ipfs", "add", "--pin=true", target_file],
            capture_output=True,
            text=True,
            check=True
        )
        
        output_lines = result.stdout.strip().split('\n')
        for line in output_lines:
            print(f"[+] IPFS BLOCK ANCHOR: {line}")
            
        print("[+] SUCCESS: Manifest permanently pinned to decentralized IPFS storage layer.")
        
    except FileNotFoundError:
        print("[!] IPFS daemon not detected in PATH. Ensure IPFS is installed and running in Termux.")
    except subprocess.CalledProcessError as e:
        print(f"[!] IPFS execution error: {e.stderr}")

if __name__ == "__main__":
    pin_manifest_to_ipfs()
