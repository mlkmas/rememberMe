# src/summarizer.py
import os
import json
import traceback
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

# --- PROMPT 1 (Simple) ---
SIMPLE_SUMMARY_PROMPT = """
You are summarizing a conversation for a person with dementia.
Rules:
- Use simple, clear language (5th grade reading level)
- Use present tense and second person ("You spoke with...")
- Identify people with their relationship ("Sarah, your daughter")
- Focus on: who they talked to, what they discussed, future plans
- Keep it under 100 words
- Be warm and reassuring in tone
- IMPORTANT: Do NOT include any people, events, or facts that are not explicitly mentioned in the transcript.

Transcript:
{transcript}

Generate simple summary:
"""

# --- PROMPT 2 (Clinical) ---
# This is the detailed JSON schema from your plan
# In src/summarizer.py

CLINICAL_JSON_SCHEMA = {
    "participant": "Name of the other person in the conversation (e.g., 'Sarah (daughter)', 'Dr. Martinez')",
    "topics_discussed": ["list of main topics, e.g., 'Family updates', 'Upcoming piano recital'"],
    
    # IMPROVED MOOD INSTRUCTIONS
    "patient_mood": "Analyze the patient's words for emotion. Choose one: 'positive' (e.g., 'I'm happy', laughing), 'neutral' (e.g., factual statements), 'anxious' (e.g., worrying), 'confused', 'agitated', 'negative' (e.g., 'my knee hurts', 'I'm sad').",
    
    "cognitive_state": "one-sentence summary of patient's performance, e.g., 'Engaged, but repeated questions about the date.'",
    "key_concerns": ["list of clinical concerns, e.g., 'Repeated a question', 'Showed memory lapse about a recent event', 'Expressed physical pain', 'Showed confusion about time/place'"]
}

# Note: This is NOT an f-string (no 'f' at the beginning)
# This is a template, which we will .format() later.
CLINICAL_SUMMARY_PROMPT = """
You are a clinical assistant analyzing a conversation involving a dementia patient.
The patient is one of the speakers.
Analyze the transcript and provide a clinical summary.
Respond ONLY with a valid JSON object that adheres to the following schema:
{schema}

Transcript:
{transcript}
"""

# --- FUNCTION 1 (Simple) ---
def summarize_transcript_simple(transcript: str) -> str:
    """
    Generates a simple, patient-facing summary from a transcript.
    """
    if not client: 
        return "Error: OpenAI client not initialized."
    if not transcript: 
        return "Error: No transcript."

    print("🧠 Generating simple summary...")
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": SIMPLE_SUMMARY_PROMPT.format(transcript=transcript)
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
    """
    Generates a structured clinical summary from a transcript.
    Returns a dictionary matching the schema or an error dict.
    """
    if not client: 
        return {"error": "OpenAI client not initialized."}
    if not transcript: 
        return {"error": "No transcript provided."}

    print("🩺 Generating clinical summary...")
    
    # Format the prompt with our schema
    prompt_content = CLINICAL_SUMMARY_PROMPT.format(
        schema=json.dumps(CLINICAL_JSON_SCHEMA, indent=2),
        transcript=transcript
    )
    
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo-1106", 
            response_format={ "type": "json_object" },
            messages=[
                {
                    "role": "system",
                    "content": prompt_content
                }
            ]
        )
        
        clinical_data = json.loads(completion.choices[0].message.content)
        print("✅ Clinical summary complete!")
        return clinical_data

    except Exception as e:
        print(f"❌❌❌ FULL TRACEBACK ... ❌❌❌")
        traceback.print_exc()
        print(f"❌❌❌ ... END TRACEBACK ❌❌❌")
        
        # Return a dict with the expected keys so the app doesn't crash
        return {
            "participant": "Error",
            "topics_discussed": [],
            "patient_mood": "error",
            "cognitive_state": f"Error in summarization: {e}",
            "key_concerns": ["Error processing transcript"]
        }

# --- Test this module independently ---
if __name__ == "__main__":
    print("--- Testing Summarizer Module ---")
    
    test_transcript = """
    Hi, this is the first test of RememberMe project. I'm talking to my
    daughter Sarah. She said she is coming to visit on Thursday.
    Patient: "Oh, what day is it today?"
    Sarah: "It's Monday, Mom. I'll see you Thursday."
    Patient: "Thursday? Okay. What day is it now?"
    Sarah: "It's still Monday, Mom. I love you."
    Patient: "I love you too. I'm just so tired and my knee hurts."
    """
    
    print("\n--- Testing Simple Summary ---")
    simple_summary = summarize_transcript_simple(test_transcript)
    print(simple_summary)
    
    print("\n--- Testing Clinical Summary ---")
    clinical_summary = summarize_transcript_clinical(test_transcript)
    print(json.dumps(clinical_summary, indent=2))