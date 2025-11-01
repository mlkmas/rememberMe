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
# PATIENT SUMMARY (for patient to hear)
# ========================================

SIMPLE_SUMMARY_PROMPT = """
You are summarizing a conversation for a person with dementia.

**CRITICAL RULES:**
1. **YOU MUST ONLY USE FACTS EXPLICITLY STATED IN THE TRANSCRIPT BELOW.**
2. **DO NOT INVENT, ASSUME, OR ADD ANY INFORMATION NOT IN THE TRANSCRIPT.**
3. **DO NOT mention people who are not explicitly named in the transcript.**
4. **Use simple, clear language (5th grade level).**
5. **Keep it under 50 words.**
6. **Address the patient directly using "you" (e.g., "You spoke with Sarah").**

**Known People (use ONLY if they appear in transcript):**
{known_people}

**THE TRANSCRIPT (your ONLY source of truth):**
{transcript}

**Generate simple summary for patient (FACTS ONLY):**
"""

# ========================================
# NEW: CAREGIVER SUMMARY (for dashboard)
# ========================================

CAREGIVER_SUMMARY_PROMPT = """
You are summarizing a conversation for a CAREGIVER monitoring a dementia patient.

**CRITICAL RULES:**
1. **YOU MUST ONLY USE FACTS EXPLICITLY STATED IN THE TRANSCRIPT BELOW.**
2. **DO NOT INVENT, ASSUME, OR ADD ANY INFORMATION NOT IN THE TRANSCRIPT.**
3. **Write in third person ABOUT the patient (use "patient", "they", "them").**
4. **Use clinical but compassionate language.**
5. **Keep it under 75 words.**
6. **Include relevant behavioral observations.**

**Examples:**
- GOOD: "Patient spoke with their daughter Sarah about upcoming visit. Patient asked about Sarah's children multiple times, showing some repetitive questioning."
- BAD: "You talked to Sarah" (that's for patient, not caregiver)

**Known People (use ONLY if they appear in transcript):**
{known_people}

**THE TRANSCRIPT (your ONLY source of truth):**
{transcript}

**Generate caregiver summary (third person, FACTS ONLY):**
"""

# ========================================
# CLINICAL SUMMARY SCHEMA
# ========================================

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
            "description": "Based ONLY on words in transcript. Choose: 'positive', 'neutral', 'anxious', 'confused', or 'unknown'."
        },
        "cognitive_state": {
            "type": "string",
            "description": "One sentence based ONLY on what was said. If transcript is too short, write: 'Insufficient data from recording'."
        },
        "key_concerns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List ONLY concerns explicitly mentioned. If none, use empty array. DO NOT INVENT CONCERNS."
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
    """Generate simple patient-facing summary"""
    if not client:
        return "Error: OpenAI client not initialized."
    if not transcript or len(transcript.strip()) < 10:
        return "The recording was too short or unclear."

    print("🧠 Generating patient summary...")

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
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": SIMPLE_SUMMARY_PROMPT.format(
                        transcript=transcript,
                        known_people=formatted_people
                    )
                }
            ],
            temperature=0.1,
            max_tokens=100
        )
        summary = completion.choices[0].message.content.strip()

        if len(summary) > 200:
            print("⚠️ Summary too long, truncating.")
            summary = summary[:197] + "..."

        print("✅ Patient summary complete!")
        return summary

    except Exception as e:
        print(f"❌ Error during patient summarization: {e}")
        return "Error creating summary."

def summarize_transcript_caregiver(transcript: str) -> str:
    """NEW: Generate caregiver-facing summary (third person)"""
    if not client:
        return "Error: OpenAI client not initialized."
    if not transcript or len(transcript.strip()) < 10:
        return "Recording too short or unclear to analyze."

    print("🩺 Generating caregiver summary...")

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
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": CAREGIVER_SUMMARY_PROMPT.format(
                        transcript=transcript,
                        known_people=formatted_people
                    )
                }
            ],
            temperature=0.1,
            max_tokens=150
        )
        summary = completion.choices[0].message.content.strip()

        if len(summary) > 300:
            print("⚠️ Caregiver summary too long, truncating.")
            summary = summary[:297] + "..."

        print("✅ Caregiver summary complete!")
        return summary

    except Exception as e:
        print(f"❌ Error during caregiver summarization: {e}")
        return "Error creating caregiver summary."

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

    print("🩺 Generating clinical summary...")

    prompt_content = CLINICAL_SUMMARY_PROMPT.format(
        transcript=transcript,
        schema=json.dumps(CLINICAL_JSON_SCHEMA, indent=2)
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt_content}
            ],
            temperature=0.1,
            max_tokens=300
        )

        clinical_data = json.loads(completion.choices[0].message.content)

        required_fields = ["participant", "topics_discussed", "patient_mood", "cognitive_state", "key_concerns"]
        for field in required_fields:
            if field not in clinical_data:
                clinical_data[field] = "Unknown" if field != "key_concerns" else []

        print("✅ Clinical summary complete!")
        return clinical_data

    except Exception as e:
        print(f"❌ Error in clinical summarization:")
        traceback.print_exc()

        return {
            "participant": "Error",
            "topics_discussed": ["Error processing"],
            "patient_mood": "unknown",
            "cognitive_state": f"Error in summarization: {e}",
            "key_concerns": ["Error processing transcript"]
        }