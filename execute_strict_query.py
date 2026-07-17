import os
import sys
import time
import glob
from google import genai
from google.genai import types

def find_target_file() -> str:
    # Auto-detect likely files in the current directory, sorted by newest first
    patterns = ["*544*", "*ledger*", "*abstract*", "*.txt", "*.log", "*.json"]
    candidates = []
    for pattern in patterns:
        candidates.extend(glob.glob(pattern))
        candidates.extend(glob.glob(f"**/{pattern}", recursive=True))
    
    # Filter out scripts and directories
    valid_files = [
        f for f in set(candidates) 
        if os.path.isfile(f) and not f.endswith(".py")
    ]
    
    if not valid_files:
        return ""
        
    # Return the most recently modified file
    valid_files.sort(key=os.path.getmtime, reverse=True)
    return valid_files[0]

def execute_strict_query(payload: str) -> str:
    if not os.environ.get("GEMINI_API_KEY"):
        return '{"error": "GEMINI_API_KEY environment variable not set."}'

    models = ["gemini-3.5-flash", "gemini-3.1-flash-lite"]
    client = genai.Client()
    
    config = types.GenerateContentConfig(
        system_instruction="You are a deterministic data processor. Output only the requested data. No conversational text.",
        temperature=0.0,
        response_mime_type="application/json",
    )

    last_err = ""
    for model_name in models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=payload,
                    config=config
                )
                return response.text
            except Exception as e:
                last_err = str(e)
                if "503" in last_err or "429" in last_err:
                    time.sleep(2 ** attempt)
                    continue
                break
                
    return f'{{"error": "All model endpoints exhausted. Last error: {last_err}"}}'

if __name__ == "__main__":
    # 1. Check for piped stdin
    if not sys.stdin.isatty():
        target_payload = sys.stdin.read().strip()
    # 2. Check for file path passed as argument
    elif len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                target_payload = f.read()
        else:
            print(f'{{"error": "Specified file not found: {file_path}"}}')
            sys.exit(1)
    # 3. Auto-detect file in directory
    else:
        detected_file = find_target_file()
        if detected_file:
            print(f'{{"status": "processing_detected_file", "file": "{detected_file}"}}', file=sys.stderr)
            with open(detected_file, "r") as f:
                file_content = f.read()
            target_payload = f"Context data:\n{file_content}\n\nTask: Extract the current state root from the Abstract 544 ledger logs."
        else:
            print('{"error": "No data in stdin, no argument provided, and no matching log/txt/json files found in directory."}')
            sys.exit(1)
        
    print(execute_strict_query(target_payload))
