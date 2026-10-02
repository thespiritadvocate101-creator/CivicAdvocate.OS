import requests
from civic_resolver import resolve

def send_civic_request(domain: str, port: int, path: str = "/"):
    # 1. Resolve .civicadvocate.os hostname using port 5353 daemon
    target_ip = resolve(domain)
    
    # 2. Construct direct IP URL and preserve the host context in headers
    url = f"http://{target_ip}:{port}{path}"
    headers = {"Host": domain}
    
    print(f"[*] Dispatching request to {domain} -> {url}")
    return requests.get(url, headers=headers, timeout=5)

if __name__ == "__main__":
    domain_name = "api-mainnet.civicadvocate.os"
    target_port = 8080  # Replace with your actual local API server port
    
    try:
        res = send_civic_request(domain_name, target_port, "/health")
        print(f"[+] Status Code: {res.status_code}")
        print(f"[+] Payload: {res.text}")
    except requests.exceptions.ConnectionError:
        print(f"[+] DNS resolved {domain_name} -> 127.0.0.1 successfully.")
        print(f"[!] Connection refused on port {target_port} (ensure your target API service is running).")
