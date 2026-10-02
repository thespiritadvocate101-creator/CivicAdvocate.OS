import socket

print("[*] Scanning local listening TCP ports on 127.0.0.1...")
open_ports = []

for port in range(1, 10000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.01)
    if s.connect_ex(('127.0.0.1', port)) == 0:
        open_ports.append(port)
    s.close()

print(f"[+] Active Listening Ports: {open_ports}")
