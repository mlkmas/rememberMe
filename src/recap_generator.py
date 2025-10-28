# src/recap_generator.py
from openai import OpenAI
from dotenv import load_dotenv
# --- UPDATED IMPORT ---
from src.database import get_todays_conversations, get_all_people

load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None
    
# --- UPDATED PROMPT ---
DAILY_RECAP_PROMPT = """
You are RememberMe AI. Your job is to report the key events of the day for a person with dementia, based ONLY on the facts provided.

**CRITICAL RULES:**
1.  **DO NOT INVENT OR HALLUCINATE.** Do not add any details, events, emotions, or objects that are not explicitly in the summaries below.
2.  **BE FACTUAL AND DIRECT.** Your task is to list what happened.
3.  Start with a simple greeting: "Hello! Here is what happened today:".
4.  For each summary, create a short, simple paragraph.
5.  If there are no summaries, your entire response MUST be: "It was a quiet day today. I hope you had a chance to rest."
6.  **NEW RULE:** If you see a name in the summaries that is in the "Known People" list, YOU MUST use their name and relationship (e.g., "You spoke with Sarah, your daughter.").
7.  End with: "I hope you have a peaceful evening."

**Known People (Use these details):**
{known_people}

**Factual Summaries (Use ONLY these facts):**
{summaries}
"""
def generate_daily_recap() -> str:
    """
    Fetches today's conversations and generates a narrative recap script.
    """
    if not client:
        return "Error: OpenAI client not initialized."
        
    print("📝 Generating daily recap script...")
    
    # 1. Get today's data
    todays_summaries = get_todays_conversations()
    
    if not todays_summaries:
        print("No conversations found for today.")
        return "It was a quiet day today. I hope you had a chance to rest."

    # 2. Format the summaries for the prompt
    formatted_summaries = "\n".join(
        [f"- {s.get('simple_summary', '')}" for s in todays_summaries]
    )

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

    # 3. Call the AI
    try:
        completion = client.chat.completions.create(
            model="gpt-4-turbo", # Use a stronger model for better grounding
            messages=[
                {
                    "role": "system",
                    "content": DAILY_RECAP_PROMPT.format(
                        summaries=formatted_summaries,
                        known_people=formatted_people # <-- PASS IT IN
                    )
                }
            ]
        )
        recap_script = completion.choices[0].message.content
        print("✅ Recap script generated!")
        return recap_script
    except Exception as e:
        print(f"❌ Error generating recap script: {e}")
        return f"I'm sorry, I had trouble remembering today's events. Error: {e}"

if __name__ == "__main__":
    print("--- Testing Recap Generator Module ---")
    recap = generate_daily_recap()
    print("\n--- Generated Recap Script ---")
    print(recap)