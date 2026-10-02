import socket
import ssl

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

print("[*] Initiating TLS handshake with 127.0.0.1:8872...")

try:
    raw_sock = socket.create_connection(('127.0.0.1', 8872), timeout=3)
    tls_sock = context.wrap_socket(raw_sock, server_hostname='localhost')
    print("[+] TLS Handshake SUCCESSFUL on port 8872!")
    print(f"[+] Active Cipher: {tls_sock.cipher()}")
    
    # Send standard HTTPS request over the TLS wrapper
    tls_sock.write(b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
    response = tls_sock.read(1024)
    print(f"[+] HTTPS Response Received:\n{response.decode('utf-8', errors='ignore')[:300]}")
    tls_sock.close()
except ssl.SSLError as e:
    print(f"[!] TLS Handshake Failed (Service does not use SSL/TLS): {e}")
except socket.timeout:
    print("[!] TLS Handshake timed out (Service did not respond to TLS Client Hello).")
except Exception as e:
    print(f"[!] Connection error: {e}")
