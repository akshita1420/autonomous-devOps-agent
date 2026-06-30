from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from brain import client, AnalysisResult # We import the client and structural template directly
from google.genai import types
# Import our new database memory functions from Step 4!
from memory import find_similar_incidents, save_incident 

app = FastAPI(title="Autonomous DevOps AI Service")

class LogRequest(BaseModel):
    log_text: str

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "AI Service Memory Routing is Active!"}

@app.post("/diagnose", response_model=AnalysisResult)
def diagnose_pipeline_failure(request: LogRequest):
    if not request.log_text.strip():
        raise HTTPException(status_code=400, detail="Log text cannot be empty.")
    
    try:
        # 1. Look into our Supabase vector memory to see if this has happened before
        historical_matches = find_similar_incidents(request.log_text, limit=1)
        
        # 2. Build a context string based on whether we found a match or not
        memory_context = ""
        if historical_matches:
            best_match = historical_matches[0]
            # If the match is high enough (e.g., above 70% match), share it with the AI brain
            if best_match["similarity"] >= 0.70:
                memory_context = f"""
                [HISTORICAL MEMORY FOUND]
                A similar issue happened in the past:
                - Past Root Cause: {best_match['root_cause']}
                - Past Fix: {best_match['suggested_fix']}
                Use this context to help guide your current diagnosis if relevant.
                """

        # 3. Formulate the comprehensive prompt for Gemini
        prompt = f"""
        Analyze the following build error log and determine what went wrong.
        {memory_context}
        
        Current Failing Log:
        {request.log_text}
        """
        
        # 4. Generate the structured decision via Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnalysisResult,
                temperature=0.1,
            ),
        )
        
        analysis = AnalysisResult.model_validate_json(response.text)
        
        # 5. Long-term Learning: If the AI is highly confident in its fix (e.g., above 85%), 
        # save this new instance automatically into our memory for future encounters!
        if analysis.confidence_score >= 0.85:
            save_incident(
                log_text=request.log_text,
                root_cause=analysis.root_cause,
                suggested_fix=analysis.suggested_fix
            )
            
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))