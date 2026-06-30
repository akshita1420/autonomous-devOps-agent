import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# 1. Load the secret API key from the .env file
load_dotenv()

# 2. Define the exact layout we want the AI to reply with.
# Instead of conversational chat, the AI MUST fill out this exact form.
class AnalysisResult(BaseModel):
    root_cause: str = Field(description="A brief, one-sentence summary of what broke.")
    suggested_fix: str = Field(description="The exact technical step needed to fix this issue.")
    confidence_score: float = Field(description="A number between 0.0 and 1.0 indicating how sure you are.")

# 3. Initialize the Google Gemini Client
client = genai.Client()

def analyze_log(log_text: str) -> AnalysisResult:
    """Sends raw log text to Gemini and demands a structured JSON response."""
    
    prompt = f"Analyze the following build error log and determine what went wrong:\n\n{log_text}"
    
    # 4. Ask Gemini to think. We use 'gemini-2.5-flash' because it is fast and free.
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            # This line forces Gemini to return JSON matching our Pydantic layout above
            response_mime_type="application/json",
            response_schema=AnalysisResult,
            temperature=0.1, # Low temperature makes the AI more predictable and less creative
        ),
    )
    
    # 5. Take the raw text response and convert it back into our clean Python structure
    return AnalysisResult.model_validate_json(response.text)

# --- TEST RUN ---
if __name__ == "__main__":
    # Let's pretend a GitHub workflow failed with this error log:
    mock_failed_log = """
    [INFO] Scanning for projects...
    [ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.11.0:compile
    [ERROR] DynamicTest.java:[12,24] fatal error: Invalid source release: 21
    [ERROR] The requested JDK version 21 is not available in the current environment environment.
    """
    
    print("Sending log to Gemini Brain...")
    result = analyze_log(mock_failed_log)
    
    print("\n--- AI Analysis Complete ---")
    print(f"Root Cause: {result.root_cause}")
    print(f"Suggested Fix: {result.suggested_fix}")
    print(f"Confidence Score: {result.confidence_score}")