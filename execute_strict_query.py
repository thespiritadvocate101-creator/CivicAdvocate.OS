import os
import sys
from google import genai
from google.genai import types

def execute_strict_query(payload: str) -> str:
    if not os.environ.get("GEMINI_API_KEY"):
        return '{"error": "GEMINI_API_KEY environment variable not set. Run: export GEMINI_API_KEY=\'your_key\'"}'

    try:
        client = genai.Client()
        
        config = types.GenerateContentConfig(
            system_instruction="You are a deterministic data processor. Output only the requested data. No conversational text.",
            temperature=0.0,
            response_mime_type="application/json",
        )
        
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=payload,
            config=config
        )
        
        return response.text
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'

if __name__ == "__main__":
    # Accept data via stdin pipe, fallback to default ledger query if run directly
    if not sys.stdin.isatty():
        target_payload = sys.stdin.read().strip()
    else:
        target_payload = "Extract the current state root from the Abstract 544 ledger logs."
        
    print(execute_strict_query(target_payload))
