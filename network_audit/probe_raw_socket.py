import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2.0)

try:
    s.connect(('127.0.0.1', 8872))
    print("[+] Successfully established TCP connection to 127.0.0.1:8872")
    
    # Check if server sends an immediate handshake/banner
    data = s.recv(1024)
    if data:
        print(f"[+] Raw Banner Received: {data}")
    else:
        print("[!] Server closed connection without data.")
except socket.timeout:
    print("[!] Connected, but server did not send an automatic banner within 2s.")
except Exception as e:
    print(f"[!] Socket connection error: {e}")
finally:
    s.close()
