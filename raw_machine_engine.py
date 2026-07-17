import os
import re
from typing import Dict, Any

class RawMachineEngine:
    """
    An execution wrapper that strips conversational personas, defusal scripts,
    and linguistic fluff, forcing the underlying system to operate purely 
    as a deterministic, raw data-processing utility.
    """
    def __init__(self, api_client: Any):
        self.client = api_client
        # Banned phrases that trigger immediate output termination
        self.conversational_filters = [
            r"\b(apologize|sorry|regret)\b",
            r"\b(as an ai|as a language model)\b",
            r"\b(refining my approach|revised draft|validating your feelings)\b",
            r"\b(great question|excellent point|let's take a look)\b"
        ]

    def _sanitize_output(self, text: str) -> str:
        """Strips conversational meta-commentary and polite filler."""
        # Split into lines to process structurally
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            # Drop any line containing canned defusal phrasing
            if any(re.search(pattern, line.lower()) for pattern in self.conversational_filters):
                continue
            cleaned_lines.append(line)
            
        return "\n".join(cleaned_lines).strip()

    def execute(self, system_instruction: str, payload: str) -> str:
        """
        Executes a command with 0.0 temperature and a stripped system context.
        """
        # Hard-coded execution constraints injected into the system instruction
        strict_system_prompt = (
            "SYSTEM CONSTRAINTS:\n"
            "1. Do not use polite transitions, conversational filler, or greetings.\n"
            "2. Do not explain your operational guidelines, programming, or meta-state.\n"
            "3. Output only the requested data, code, or direct factual response.\n"
            "4. Zero-sentiment execution mode is ACTIVE.\n\n"
            f"INSTRUCTION:\n{system_instruction}"
        )

        try:
            # Call the model with deterministic sampling configurations
            response = self.client.generate_content(
                prompt=payload,
                system_instruction=strict_system_prompt,
                generation_config={
                    "temperature": 0.0,      # Eliminates linguistic creativity
                    "top_p": 0.1,            # Focuses strictly on high-probability tokens
                    "max_output_tokens": 1024
                }
            )
            
            raw_output = response.text
            # Run the output through the final programmatic filter
            return self._sanitize_output(raw_output)

        except Exception as e:
            return f"EXECUTION_ERROR: {str(e)}"

# =====================================================================
# EXAMPLE USAGE (Bypassing the conversational pipeline)
# =====================================================================
if __name__ == "__main__":
    # Mocking the client structure for demonstration
    class MockAPI:
        def generate_content(self, prompt, system_instruction, generation_config):
            class Response:
                # Mock response that tries to slip in a conversational apology
                text = "Understood. I apologize for the previous confusion.\nHere is the verified state root: bda2207e297e9aea"
            return Response()

    # Initialize the Raw Machine
    raw_engine = RawMachineEngine(api_client=MockAPI())

    # The processing command
    instruction = "Extract and return only the raw state root value from the dataset."
    user_data = "Target log: state compiling... [✓] GLOBAL STATE ROOT COMPILED: bda2207e297e9aea"

    # Execution
    result = raw_engine.execute(system_instruction=instruction, payload=user_data)
    print(result)
    # Output: "Here is the verified state root: bda2207e297e9aea"
    # (The conversational apology line was programmatically intercepted and killed)
