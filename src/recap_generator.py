"""
Module for generating a daily recap narrative from conversation summaries.
"""
from openai import OpenAI
from dotenv import load_dotenv
from src.database import get_todays_conversations

load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None
    
# In src/recap_generator.py

# THE FIX: We are changing the AI's job from "Storyteller" to "Factual Reporter"
DAILY_RECAP_PROMPT = """
You are RememberMe AI. Your job is to report the key events of the day for a person with dementia, based ONLY on the facts provided.

**CRITICAL RULES:**
1.  **DO NOT INVENT OR HALLUCINATE.** Do not add any details, events, emotions, or objects that are not explicitly in the summaries below.
2.  **BE FACTUAL AND DIRECT.** Your task is to list what happened, not to tell a creative story.
3.  Start with a simple greeting: "Hello! Here is what happened today:".
4.  For each summary, create a short, simple paragraph.
5.  If there are no summaries, your entire response MUST be: "It was a quiet day today. I hope you had a chance to rest."
6.  End with: "I hope you have a peaceful evening."

Here are the factual summaries from today. Use ONLY these facts:
{summaries}
"""
def generate_daily_recap() -> str:
    """
    Fetches today's conversations and generates a narrative recap script.
    """
    if not client:
        return "Error: OpenAI client not initialized."
        
    print("📝 Generating daily recap script...")
    
    # 1. Get today's data from the database
    todays_summaries = get_todays_conversations()
    
    if not todays_summaries:
        print("No conversations found for today.")
        return "It was a quiet day today. I hope you had a chance to rest."

    # 2. Format the data for the prompt
    formatted_summaries = "\n".join(
        [f"- {s.get('simple_summary', '')}" for s in todays_summaries]
    )

    # 3. Call the AI to write the story
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": DAILY_RECAP_PROMPT.format(summaries=formatted_summaries)
                }
            ]
        )
        recap_script = completion.choices[0].message.content
        print("✅ Recap script generated!")
        return recap_script
    except Exception as e:
        print(f"❌ Error generating recap script: {e}")
        return f"I'm sorry, I had trouble remembering today's events. Error: {e}"

# --- Test this module independently ---
if __name__ == "__main__":
    print("--- Testing Recap Generator Module ---")
    # This will connect to your actual database to test
    recap = generate_daily_recap()
    print("\n--- Generated Recap Script ---")
    print(recap)
    print("----------------------------")
