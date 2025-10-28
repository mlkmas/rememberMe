# src/summarizer.py
import os
import json
import traceback
from openai import OpenAI
from dotenv import load_dotenv
# --- UPDATED IMPORT ---
from src.database import get_all_people

load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

# --- UPDATED PROMPT 1 (Simple) ---
SIMPLE_SUMMARY_PROMPT = """
You are summarizing a conversation for a person with dementia.
Rules:

**CRITICAL RULE: You MUST ONLY use information explicitly present in the transcript.**
- Use simple, clear language (5th grade reading level)
- **NEW RULE:** If you see a name that is in the "Known People" list, YOU MUST use their name and relationship (e.g., "Sarah, your daughter").
- Focus on: who they talked to, what they discussed, future plans
- Keep it under 100 words
- Be warm and reassuring in tone
- IMPORTANT: Do NOT include any people, events, or facts that are not explicitly mentioned in the transcript.

**Known People (Use these details):**
{known_people}

Transcript:
{transcript}

Generate simple summary:
"""

# --- PROMPT 2 (Clinical) ---
CLINICAL_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "participant": {
            "type": "string",
            "description": "Name of the other person if mentioned, otherwise 'Unknown' or 'Patient speaking alone'. DO NOT INVENT A NAME."
        },
        "topics_discussed": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of main topics, e.g., 'Family updates', 'Upcoming piano recital'"
        },
        "patient_mood": {
            "type": "string",
            "description": "Analyze patient's words for emotion. Choose one: 'positive', 'neutral', 'anxious', 'confused', 'agitated', 'negative'."
        },
        "cognitive_state": {
            "type": "string",
            "description": "One-sentence summary of patient's performance, e.g., 'Engaged, but repeated questions about the date.'"
        },
        "key_concerns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of clinical concerns explicitly mentioned, e.g., 'Repeated a question', 'Expressed physical pain'."
        }
    },
    "required": ["participant", "topics_discussed", "patient_mood", "cognitive_state", "key_concerns"]
}

CLINICAL_SUMMARY_PROMPT = """
You are a clinical assistant analyzing a conversation involving a dementia patient.

**CRITICAL RULE: You MUST ONLY use information explicitly present in the transcript. DO NOT HALLUCINATE OR INVENT any details. If information is not present, use 'Unknown' or an empty list.**

Analyze the transcript and provide a clinical summary. Respond ONLY with a valid JSON object that adheres to the provided schema.

Transcript:
{transcript}
"""

# --- FUNCTION 1 (Simple) ---
def summarize_transcript_simple(transcript: str) -> str:
    if not client: return "Error: OpenAI client not initialized."
    if not transcript: return "Error: No transcript."

    print("🧠 Generating simple summary...")
    
    # --- NEW: Get Known People (Step 1) ---
    try:
        people = get_all_people()
        if not people:
            formatted_people = "No people profiles available."
        else:
            formatted_people = "\n".join(
                [f"- {p.get('name')} ({p.get('relationship')})" for p in people]
            )
    except Exception as e:
        print(f"Warning: Could not fetch people list. {e}")
        formatted_people = "Error fetching people list."
    # --- END NEW ---

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": SIMPLE_SUMMARY_PROMPT.format(
                        transcript=transcript,
                        known_people=formatted_people # <-- PASS IT IN
                    )
                }
            ]
        )
        summary = completion.choices[0].message.content
        print("✅ Simple summary complete!")
        return summary
    except Exception as e:
        print(f"❌ Error during simple summarization: {e}")
        return f"Error: {e}"

# --- FUNCTION 2 (Clinical) ---
def summarize_transcript_clinical(transcript: str) -> dict:
    if not client: return {"error": "OpenAI client not initialized."}
    if not transcript: return {"error": "No transcript provided."}

    print("🩺 Generating clinical summary...")
    
    prompt_content = CLINICAL_SUMMARY_PROMPT.format(transcript=transcript)
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4-turbo", # Use a model that fully supports JSON mode
            response_format={ "type": "json_object", "schema": CLINICAL_JSON_SCHEMA },
            messages=[
                {"role": "system", "content": prompt_content}
            ]
        )
        
        clinical_data = json.loads(completion.choices[0].message.content)
        print("✅ Clinical summary complete!")
        return clinical_data

    except Exception as e:
        print(f"❌❌❌ FULL TRACEBACK ... ❌❌❌")
        traceback.print_exc()
        print(f"❌❌❌ ... END TRACEBACK ❌❌❌")
        
        # Return a dict with the expected keys
        return {
            "participant": "Error",
            "topics_discussed": [],
            "patient_mood": "error",
            "cognitive_state": f"Error in summarization: {e}",
            "key_concerns": ["Error processing transcript"]
        }

if __name__ == "__main__":
    print("--- Testing Summarizer Module ---")
    test_transcript = "Hi, this is Sarah. I'm just calling to say I love you. Patient: 'I love you too. My knee hurts.' ... Patient: 'What day is it?'"
    
    print("\n--- Testing Simple Summary ---")
    simple_summary = summarize_transcript_simple(test_transcript)
    print(simple_summary)
    
    print("\n--- Testing Clinical Summary ---")
    clinical_summary = summarize_transcript_clinical(test_transcript)
    print(json.dumps(clinical_summary, indent=2))