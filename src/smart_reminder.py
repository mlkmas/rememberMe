import os
from openai import OpenAI
from dotenv import load_dotenv
from src.database import get_todays_conversations
from src.text_to_speech import text_to_speech
from src.schemas import Medication

load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

# This is the AI "brain" for the smart reminder feature.
SMART_REMINDER_PROMPT = """
You are RememberMe AI, a friendly and reassuring assistant for a person with dementia.
Your task is to generate a script for a spoken medication reminder.

**Rules:**
1.  Start with a gentle greeting and state the time and medication name (e.g., "Hello! It's 2:00 PM, time for your Ibuprofen.").
2.  **CONTEXTUAL LINK (IMPORTANT):** Look at the recent conversation summaries. If a summary mentions a symptom (like 'pain', 'headache', 'trouble sleeping') that matches the medication's purpose, create a gentle link.
    - Example: If a conversation mentioned "knee hurts" and the medication is for "pain relief", say something like: "Earlier today, you mentioned your knee was hurting. This medication should help with that."
3.  If no relevant context is found in the conversations, DO NOT invent anything. Just state the medication's purpose simply.
    - Example: "This is the medication you take for pain relief."
4.  Keep the entire script short, clear, and under 75 words.
5.  End with a warm closing, like "Please let me know when you've taken it." or "I hope you have a wonderful afternoon."

**Medication Details:**
- Name: {med_name}
- Dosage: {med_dosage}
- Purpose: {med_purpose}
- Time: {med_time}

**Recent Conversation Summaries (for context):**
{conversation_context}

Now, generate the reminder script:
"""

def generate_smart_reminder(medication: dict) -> str | None:
    """
    Generates a context-aware audio reminder for a specific medication.

    Args:
        medication: A dictionary representing a medication from the database.

    Returns:
        The file path to the generated audio file, or None if an error occurs.
    """
    if not client:
        print("OpenAI client not initialized.")
        return None

    print(f"🧠 Generating smart reminder for {medication.get('name')}...")

    # 1. Get today's conversations for context
    todays_summaries = get_todays_conversations()
    if not todays_summaries:
        context_text = "No conversations recorded yet today."
    else:
        # Format the summaries into a simple list for the prompt
        context_text = "\n".join([f"- {s.get('simple_summary', '')}" for s in todays_summaries])

    # 2. Format the prompt with all the necessary information
    prompt = SMART_REMINDER_PROMPT.format(
        med_name=medication.get('name', 'N/A'),
        med_dosage=medication.get('dosage', 'N/A'),
        med_purpose=medication.get('purpose', 'N/A'),
        med_time=medication.get('time_to_take', 'N/A'),
        conversation_context=context_text
    )

    try:
        # 3. Call GPT to generate the script
        completion = client.chat.completions.create(
            model="gpt-4", # Using GPT-4 for better contextual understanding
            messages=[{"role": "system", "content": prompt}]
        )
        reminder_script = completion.choices[0].message.content
        print(f"📝 Generated Script: {reminder_script}")

        # 4. Call TTS to convert the script to audio
        audio_file_path = text_to_speech(reminder_script)
        
        return audio_file_path

    except Exception as e:
        print(f"❌ Error generating smart reminder: {e}")
        return None
