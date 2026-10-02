import socket
import json

PAYLOADS = [
    {"jsonrpc": "2.0", "method": "ping", "params": [], "id": 1},
    {"jsonrpc": "2.0", "method": "health", "params": [], "id": 1},
    {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
    {"action": "ping"},
    {"type": "health_check"},
]

def test_payload(payload):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect(('127.0.0.1', 8872))
        raw_data = json.dumps(payload).encode('utf-8') + b'\n'
        s.sendall(raw_data)
        
        resp = s.recv(1024)
        if resp:
            label = payload.get('method') or payload.get('action') or payload.get('type')
            print(f"[+] SUCCESS for payload '{label}':")
            print(f"    Response: {resp.decode('utf-8', errors='ignore')[:300]}\n")
            return True
    except socket.timeout:
        label = payload.get('method') or payload.get('action') or payload.get('type')
        print(f"[-] Timeout for payload: {label}")
    except Exception as e:
        print(f"[!] Socket error: {e}")
    finally:
        s.close()
    return False

if __name__ == "__main__":
    print("[*] Probing 127.0.0.1:8872 with JSON-RPC / structured payloads...\n")
    any_success = False
    for p in PAYLOADS:
        if test_payload(p):
            any_success = True
            break

    if not any_success:
        print("[!] No standard JSON-RPC payloads received a response. The service may require binary protocol framing (such as PostgreSQL, gRPC, or WebSocket handshakes).")
