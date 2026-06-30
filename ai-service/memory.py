import os
import psycopg2
from dotenv import load_dotenv
from google import genai
from google.genai import types
# Load database and API key configuration
load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
client = genai.Client()

def get_db_connection():
    """Establishes a connection to your Supabase PostgreSQL instance."""
    return psycopg2.connect(DB_URL)

def generate_embedding(text: str) -> list[float]:
    """
    Converts a text string into a 768-dimensional array of numbers (embedding)
    representing its core meaning.
    """
    # We use 'text-embedding-004', which is Google's latest standard embedding model
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    # Extract the list of float numbers from the response object
    return response.embeddings[0].values

def save_incident(log_text: str, root_cause: str, suggested_fix: str):
    """Generates an embedding for an error log and saves it to the cloud database."""
    print("Generating embedding for the new log...")
    vector = generate_embedding(log_text)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    INSERT INTO past_incidents (log_text, root_cause, suggested_fix, embedding)
    VALUES (%s, %s, %s, %s);
    """
    
    try:
        cursor.execute(query, (log_text, root_cause, suggested_fix, vector))
        conn.commit()
        print("Successfully saved incident into long-term vector memory!")
    except Exception as e:
        conn.rollback()
        print(f"Error saving to database: {e}")
    finally:
        cursor.close()
        conn.close()

def find_similar_incidents(new_log_text: str, limit: int = 2) -> list[dict]:
    """
    Takes a brand-new error log, generates its embedding, and queries Supabase
    to find past logs that have a similar meaning using Cosine Similarity.
    """
    print("Generating embedding for search query...")
    query_vector = generate_embedding(new_log_text)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We call the custom 'match_incidents' function we loaded into SQL in Step 3!
    # We use a matching threshold of 0.5 (50% similarity or better)
    cursor.execute("SELECT * FROM match_incidents(%s::vector, 0.5, %s);", (query_vector, limit))
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "log_text": row[1],
            "root_cause": row[2],
            "suggested_fix": row[3],
            "similarity": row[4]
        })
        
    cursor.close()
    conn.close()
    return results

# --- RUN A TESTS LOOP ---
if __name__ == "__main__":
    print("--- Memory Script Test Run ---")
    
    # Let's seed our database with a past memory
    past_log = "Error: OutOfMemoryError. Java heap space exhausted in target controller application."
    past_cause = "The server ran out of RAM memory because the JVM max heap size parameter (-Xmx) was too low."
    past_fix = "Increase the JVM configuration allocations to -Xmx2g in your startup execution script."
    
    save_incident(past_log, past_cause, past_fix)
    
    # Now let's try to query the database using a slightly DIFFERENT sentence structure 
    # to prove it searches by meaning (Semantic Search), not exact keyword matching!
    new_incoming_log = "CRITICAL FAILURE: The system is crashing due to insufficient Java memory heap size."
    
    print("\nSearching memory for similar past issues...")
    matches = find_similar_incidents(new_incoming_log)
    
    print(f"\nFound {len(matches)} historical match(es):")
    for match in matches:
        print(f"- [Match Confidence Score: {match['similarity']:.2f}]")
        print(f"  Past Root Cause: {match['root_cause']}")
        print(f"  Past Suggested Fix: {match['suggested_fix']}")