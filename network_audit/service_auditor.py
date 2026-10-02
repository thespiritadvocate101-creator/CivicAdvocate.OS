import socket
import subprocess
import time
import sys

# Define port-to-service mapping (Port: termux-service name)
WATCHED_SERVICES = {
    8080: "reverse_proxy",
    8085: "audit_server",
    5432: "postgresql",
}

CHECK_INTERVAL = 10  # Seconds between checks
CONNECT_TIMEOUT = 1.0  # Socket timeout in seconds

def check_port(host: str, port: int) -> bool:
    """Returns True if connection to host:port succeeds."""
    try:
        with socket.create_connection((host, port), timeout=CONNECT_TIMEOUT):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def restart_termux_service(service_name: str):
    """Triggers termux-services restart via 'sv' command."""
    print(f"[!] Target port unreachable. Restarting service: '{service_name}'...")
    try:
        result = subprocess.run(
            ["sv", "restart", service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"[+] Successfully sent restart signal to '{service_name}'.")
        else:
            print(f"[-] Failed to restart '{service_name}': {result.stderr.strip()}")
    except FileNotFoundError:
        print("[-] Error: 'sv' executable not found. Ensure 'termux-services' is installed.")
    except Exception as e:
        print(f"[-] Exception restarting '{service_name}': {e}")

def main():
    print(f"[*] Starting Service Auditor daemon [Interval: {CHECK_INTERVAL}s]")
    for port, svc in WATCHED_SERVICES.items():
        print(f"    - Monitoring Port {port} -> Service '{svc}'")
    
    try:
        while True:
            for port, service_name in WATCHED_SERVICES.items():
                is_alive = check_port("127.0.0.1", port)
                if not is_alive:
                    print(f"[WARN] Health check failed for 127.0.0.1:{port}")
                    restart_termux_service(service_name)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n[*] Service Auditor stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
