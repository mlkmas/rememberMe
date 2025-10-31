# src/summarizer.py
import os
import json
import traceback
from openai import OpenAI
from dotenv import load_dotenv
from src.database import get_all_people

load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

# ========================================
# CRITICAL: ANTI-HALLUCINATION PROMPTS
# ========================================

SIMPLE_SUMMARY_PROMPT = """
You are summarizing a conversation for a person with dementia.

**CRITICAL RULES - READ CAREFULLY:**
1. **YOU MUST ONLY USE FACTS EXPLICITLY STATED IN THE TRANSCRIPT BELOW.**
2. **DO NOT INVENT, ASSUME, OR ADD ANY INFORMATION NOT IN THE TRANSCRIPT.**
3. **DO NOT mention people who are not explicitly named in the transcript.**
4. **DO NOT describe events, plans, or conversations that are not explicitly mentioned.**
5. **If the transcript is unclear or incomplete, say "The recording was unclear" - DO NOT FILL IN GAPS.**
6. **If no one else is mentioned, write: "You were speaking alone."**
7. **Use simple, clear language (5th grade level).**
8. **Keep it under 50 words.**
9. **Be warm but FACTUAL ONLY.**

**Known People (use ONLY if they appear in transcript):**
{known_people}

**THE TRANSCRIPT (your ONLY source of truth):**
{transcript}

**Generate simple summary (FACTS ONLY, NO ASSUMPTIONS):**
"""

CLINICAL_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "participant": {
            "type": "string",
            "description": "ONLY include a name if explicitly mentioned in the transcript. If no one is mentioned, use 'Patient speaking alone'. DO NOT INVENT NAMES."
        },
        "topics_discussed": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List ONLY topics explicitly mentioned. If unclear, use ['Unclear recording']. DO NOT INVENT TOPICS."
        },
        "patient_mood": {
            "type": "string",
            "description": "Based ONLY on words in transcript. Choose: 'positive', 'neutral', 'anxious', 'confused', or 'unknown'. If unsure, use 'unknown'."
        },
        "cognitive_state": {
            "type": "string",
            "description": "One sentence based ONLY on what was said. If transcript is too short or unclear, write: 'Insufficient data from recording'."
        },
        "key_concerns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List ONLY concerns explicitly mentioned (e.g., 'Mentioned knee pain', 'Asked same question twice'). If none, use empty array. DO NOT INVENT CONCERNS."
        }
    },
    "required": ["participant", "topics_discussed", "patient_mood", "cognitive_state", "key_concerns"]
}

CLINICAL_SUMMARY_PROMPT = """
You are a clinical assistant analyzing a conversation with a dementia patient.

**CRITICAL ANTI-HALLUCINATION RULES:**
1. **YOU MUST ONLY USE INFORMATION EXPLICITLY STATED IN THE TRANSCRIPT BELOW.**
2. **DO NOT INVENT, ASSUME, GUESS, OR ADD ANY INFORMATION.**
3. **If information is missing or unclear, explicitly state "Unknown" or "Insufficient data".**
4. **DO NOT infer relationships, events, or details not explicitly mentioned.**
5. **DO NOT mention people who are not named in the transcript.**
6. **If the transcript is very short or unclear, all fields should reflect this uncertainty.**

**Example of WRONG (hallucinated) response:**
- Participant: "Sarah (daughter)" ← WRONG if "Sarah" or "daughter" not in transcript
- Topics: ["Thanksgiving plans"] ← WRONG if "Thanksgiving" not mentioned
- Concerns: ["Confusion about identity"] ← WRONG if not explicitly shown

**Example of CORRECT response:**
- Participant: "Patient speaking alone" ← CORRECT if no one else mentioned
- Topics: ["Unclear - short recording"] ← CORRECT if unclear
- Concerns: [] ← CORRECT if nothing explicit

**Schema:**
{schema}

**THE TRANSCRIPT (your ONLY source of truth):**
{transcript}

**Generate clinical summary as JSON (STRICT FACTS ONLY):**
"""


# ========================================
# SUMMARIZATION FUNCTIONS
# ========================================

def summarize_transcript_simple(transcript: str) -> str:
    """Generate simple patient-facing summary with strict anti-hallucination"""
    if not client:
        return "Error: OpenAI client not initialized."
    if not transcript or len(transcript.strip()) < 10:
        return "The recording was too short or unclear."

    print("🧠 Generating simple summary (anti-hallucination mode)...")

    # Get known people
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

    try:
        completion = client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 for better instruction following
            messages=[
                {
                    "role": "system",
                    "content": SIMPLE_SUMMARY_PROMPT.format(
                        transcript=transcript,
                        known_people=formatted_people
                    )
                }
            ],
            temperature=0.1,  # Lower temperature = less creative = less hallucination
            max_tokens=100  # Limit length to prevent elaboration
        )
        summary = completion.choices[0].message.content.strip()

        # Validation: Check if summary is reasonable length
        if len(summary) > 200:
            print("⚠️ Summary too long, likely hallucinated. Truncating.")
            summary = summary[:197] + "..."

        print("✅ Simple summary complete!")
        return summary

    except Exception as e:
        print(f"❌ Error during simple summarization: {e}")
        return "Error creating summary."


def summarize_transcript_clinical(transcript: str) -> dict:
    """Generate clinical summary with strict anti-hallucination"""
    if not client:
        return {"error": "OpenAI client not initialized."}
    if not transcript or len(transcript.strip()) < 10:
        return {
            "participant": "Patient speaking alone",
            "topics_discussed": ["Recording too short"],
            "patient_mood": "unknown",
            "cognitive_state": "Insufficient data - recording too brief",
            "key_concerns": []
        }

    print("🩺 Generating clinical summary (anti-hallucination mode)...")

    prompt_content = CLINICAL_SUMMARY_PROMPT.format(
        transcript=transcript,
        schema=json.dumps(CLINICAL_JSON_SCHEMA, indent=2)
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4",  # GPT-4 for better instruction following
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt_content}
            ],
            temperature=0.1,  # Lower = less creative = less hallucination
            max_tokens=300
        )

        clinical_data = json.loads(completion.choices[0].message.content)

        # Validation: Ensure required fields exist
        required_fields = ["participant", "topics_discussed", "patient_mood", "cognitive_state", "key_concerns"]
        for field in required_fields:
            if field not in clinical_data:
                clinical_data[field] = "Unknown" if field != "key_concerns" else []

        print("✅ Clinical summary complete!")
        return clinical_data

    except Exception as e:
        print(f"❌❌❌ FULL TRACEBACK ... ❌❌❌")
        traceback.print_exc()
        print(f"❌❌❌ ... END TRACEBACK ❌❌❌")

        return {
            "participant": "Error",
            "topics_discussed": ["Error processing"],
            "patient_mood": "unknown",
            "cognitive_state": f"Error in summarization: {e}",
            "key_concerns": ["Error processing transcript"]
        }


if __name__ == "__main__":
    print("--- Testing Anti-Hallucination Summarizer ---")

    # Test with minimal transcript
    test_transcript = "Is Sarah coming today? Where are we going? My knee hurts."

    print("\n--- Testing Simple Summary ---")
    simple_summary = summarize_transcript_simple(test_transcript)
    print(f"Result: {simple_summary}")

    print("\n--- Testing Clinical Summary ---")
    clinical_summary = summarize_transcript_clinical(test_transcript)
    print(json.dumps(clinical_summary, indent=2))