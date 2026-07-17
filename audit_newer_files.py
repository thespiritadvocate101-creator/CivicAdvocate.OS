import os
import sys
import pathlib
from datetime import datetime
from collections import defaultdict

# Add any directory names or file extensions you want to ignore
IGNORE_DIRS = {".git", ".github", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache"}
IGNORE_EXTS = {".pyc", ".pyo", ".pyd", ".db-journal"}

def run_audit(directory=".", target_date_str="2026-06-11"):
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_timestamp = target_date.timestamp()
    
    print(f"[*] Target Date Threshold: {target_date_str}")
    print(f"[*] Scanning: {os.path.abspath(directory)}\n")
    
    flagged_files = []
    total_files = 0
    script_name = os.path.basename(__file__)

    for path in pathlib.Path(directory).rglob("*"):
        if path.is_file():
            # Skip ignored directories in the path
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            if path.name == script_name or path.suffix in IGNORE_EXTS:
                continue
                
            total_files += 1
            try:
                mtime = path.stat().st_mtime
                if mtime > target_timestamp:
                    mod_time = datetime.fromtimestamp(mtime)
                    flagged_files.append({
                        "path": path,
                        "relative_path": str(path.relative_to(directory)),
                        "directory": str(path.parent.relative_to(directory)),
                        "modified": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "timestamp": mtime
                    })
            except Exception as e:
                pass

    if flagged_files:
        # Group by directory to find the source of the drift
        grouped = defaultdict(list)
        for f in flagged_files:
            grouped[f["directory"]].append(f)
            
        print(f"[!] {len(flagged_files)} files modified post-sync. Distribution by directory:")
        print("-" * 80)
        for folder, files in sorted(grouped.items()):
            folder_display = folder if folder != "." else "Root"
            print(f"📁 {folder_display}/ ({len(files)} files modified)")
            # Show up to 3 newest files in this folder to keep output clean
            sorted_files = sorted(files, key=lambda x: x["timestamp"], reverse=True)
            for f in sorted_files[:3]:
                print(f"   ↳ {os.path.basename(f['relative_path'])} ({f['modified']})")
            if len(files) > 3:
                print(f"   ↳ ... and {len(files) - 3} more")
            print()
        print("-" * 80)
        sys.exit(1)
    else:
        print(f"[✓] CLEAN: All {total_files} active files match or predate the {target_date_str} ledger state.")
        sys.exit(0)

if __name__ == "__main__":
    run_audit()
