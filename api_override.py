import google.generativeai as genai

# 1. Overwrite the default behavior at the system level
# This replaces the hidden rules that tell the model to be a "helpful assistant"
strict_instruction = "You are a deterministic data processor. Output only the requested data. No conversational text."

# 2. Force the model to output ONLY valid JSON
# If the network tries to generate "Here is your data:", it fails validation and is suppressed.
config = genai.types.GenerationConfig(
    temperature=0.0,
    response_mime_type="application/json",
)

# 3. Initialize the model with the overrides
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction=strict_instruction,
    generation_config=config
)

payload = "Extract the current state root from the Abstract 544 ledger logs."
response = model.generate_content(payload)

print(response.text)
