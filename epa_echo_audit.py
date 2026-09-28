#!/usr/bin/env python3
import time
import urllib.request
import urllib.error
import json
import os

def query_epa_with_backoff(url, max_retries=4, initial_delay=2):
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'CivicAdvocate.OS-Auditor/1.0 (Architect@CivicAdvocate)'}
            )
            print(f"[*] Querying endpoint (Attempt {attempt + 1}/{max_retries})...")
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"[!] Rate limit (429) hit. Backing off for {delay} seconds...")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"[!] HTTP Error {e.code}: {e.reason}")
                return None
        except Exception as e:
            print(f"[!] Connection Exception: {e}")
            return None
    print("[!] Max retries exceeded for EPA endpoint.")
    return None

def run_audit():
    print("[*] Initializing EPA FRS spatial audit for Abstract 544...")
    target_url = "https://ofmpub.epa.gov/frs_public2/frs_rest_services.get_facilities?latitude83=32.42&longitude83=-97.38&search_radius=5&output=JSON"
    data = query_epa_with_backoff(target_url)
    if data:
        with open("epa_facilities_audit.json", "w") as f:
            json.dump(data, f, indent=2)
        print("[+] SUCCESS: EPA audit data successfully retrieved and recorded to epa_facilities_audit.json")
    else:
        print("[!] Audit query failed or returned empty payload.")

if __name__ == "__main__":
    run_audit()
