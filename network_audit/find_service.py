import os

print("[*] Auditing running background processes in Termux...")
found = 0
for pid in os.listdir('/proc'):
    if pid.isdigit():
        try:
            cmdline_path = os.path.join('/proc', pid, 'cmdline')
            with open(cmdline_path, 'rb') as f:
                cmd = f.read().replace(b'\x00', b' ').decode('utf-8', errors='ignore').strip()
            if cmd and ('python' in cmd or 'node' in cmd or 'CivicAdvocate' in cmd or 'postgres' in cmd or 'pg_' in cmd):
                print(f"[+] PID {pid}: {cmd}")
                found += 1
        except (PermissionError, FileNotFoundError):
            continue

if found == 0:
    print("[!] No matching user processes found.")
