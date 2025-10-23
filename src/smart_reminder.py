import os
from openai import OpenAI
from dotenv import load_dotenv
# Corrected import name based on previous steps
from src.database import get_todays_conversations
from src.text_to_speech import text_to_speech
# We don't strictly need Medication schema here, but can use dict
# from src.schemas import Medication

load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

# This is the AI "brain" for the smart reminder feature.
SMART_REMINDER_PROMPT = """
You are RememberMe AI, a friendly and reassuring assistant for a person with dementia.
Your task is to generate a script for a spoken medication reminder based ONLY on the information provided.

**CRITICAL RULES:**
1.  **DO NOT HALLUCINATE OR INVENT.** Do not add any details, events, emotions, symptoms, or objects that are not explicitly in the medication details or conversation summaries below.
2.  Start with a gentle greeting and state the time and medication name (e.g., "Hello! It's 2:00 PM, time for your Ibuprofen.").
3.  **CONTEXTUAL LINK (IF POSSIBLE):** Look at the recent conversation summaries. If a summary explicitly mentions a symptom (like 'pain', 'headache', 'trouble sleeping', 'knee hurts') that perfectly matches the medication's purpose, create a simple, direct link.
    - Example: If a conversation summary says "Mentioned knee pain" and the medication purpose is "pain relief", say: "This is the medication for pain relief. Earlier today, you mentioned your knee was hurting."
4.  If no explicit, perfectly matching context is found, DO NOT try to force a link. Just state the medication's purpose simply.
    - Example: "This is the medication you take for pain relief."
5.  Keep the entire script short, clear, and under 75 words.
6.  End with a warm, simple closing like "Please take it now." or "I hope this helps you feel better."

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
        The file path to the generated audio file (str), or None if an error occurs.
    """
    if not client:
        print("❌ OpenAI client not initialized.")
        return None

    print(f"🧠 Generating smart reminder for {medication.get('name')}...")

    # 1. Get today's conversations for context
    todays_summaries = get_todays_conversations()
    if not todays_summaries:
        context_text = "No conversations recorded yet today."
    else:
        # Format the summaries and clinical concerns into a simple list for the prompt
        context_items = []
        for s in todays_summaries:
            context_items.append(f"- Summary: {s.get('simple_summary', '')}")
            concerns = s.get('key_concerns', [])
            if concerns:
                 context_items.append(f"  - Concerns noted: {', '.join(concerns)}")
        context_text = "\n".join(context_items)


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
        print("🤖 Calling GPT to generate reminder script...")
        completion = client.chat.completions.create(
            # Using GPT-4 for better adherence to instructions and context linking
            model="gpt-4", 
            messages=[{"role": "system", "content": prompt}]
        )
        reminder_script = completion.choices[0].message.content
        if not reminder_script:
             raise ValueError("GPT returned an empty script.")
        print(f"📝 Generated Script: {reminder_script}")

        # 4. Call TTS to convert the script to audio
        print("🔊 Calling TTS to generate audio...")
        audio_file_path = text_to_speech(reminder_script) # text_to_speech returns Path object
        
        if audio_file_path:
             print(f"✅ Audio file generated at: {audio_file_path}")
             return str(audio_file_path) # Convert Path to string for session state
        else:
             raise Exception("Text-to-speech conversion failed.")

    except Exception as e:
        import traceback
        print(f"❌ Error generating smart reminder:")
        traceback.print_exc()
        return None
