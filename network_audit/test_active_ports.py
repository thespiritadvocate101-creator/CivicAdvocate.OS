import requests
from civic_resolver import resolve

target_ip = resolve('api-mainnet.civicadvocate.os')

for port in [8085, 8872]:
    print(f"[*] Testing port {port}...")
    try:
        res = requests.get(f'http://{target_ip}:{port}/', headers={'Host': 'api-mainnet.civicadvocate.os'}, timeout=3)
        print(f"[+] Port {port} Status Code: {res.status_code}")
        print(f"[+] Response Body:\n{res.text[:300]}\n")
    except Exception as e:
        print(f"[!] Port {port} connection error: {e}\n")
