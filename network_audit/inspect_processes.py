import os

print(f"{'PID':<8} {'COMMAND'}")
print("-" * 60)
for pid in sorted(os.listdir('/proc'), key=lambda x: int(x) if x.isdigit() else 999999):
    if pid.isdigit():
        try:
            cmdline_path = os.path.join('/proc', pid, 'cmdline')
            with open(cmdline_path, 'rb') as f:
                cmd = f.read().replace(b'\x00', b' ').decode('utf-8', errors='ignore').strip()
            if cmd and not cmd.startswith('['):  # Filter kernel threads
                print(f"{pid:<8} {cmd[:80]}")
        except (PermissionError, FileNotFoundError):
            continue
