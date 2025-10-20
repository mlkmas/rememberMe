"""
Module for summarizing transcripts using OpenAI's GPT models.
"""
from openai import OpenAI
from dotenv import load_dotenv

# This will load the OPENAI_API_KEY from your .env file
load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

# This is the prompt you designed in your project plan!
SIMPLE_SUMMARY_PROMPT = """
You are summarizing a conversation for a person with dementia.

Rules:
- Use simple, clear language (5th grade reading level)
- Use present tense and second person ("You spoke with...")
- Identify people with their relationship ("Sarah, your daughter")
- Focus on: who they talked to, what they discussed, future plans
- Keep it under 100 words
- Be warm and reassuring in tone

Transcript:
{transcript}

Generate simple summary:
"""

def summarize_transcript(transcript: str) -> str:
    """
    Generates a simple, patient-facing summary from a transcript.
    """
    if not client:
        return "Error: OpenAI client not initialized."
    
    if not transcript:
        return "Error: No transcript provided to summarize."

    print("🧠 Generating simple summary...")

    try:
        # This is the "Week 2" part: calling the chat API
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Or "gpt-3.5-turbo" for faster/cheaper
            messages=[
                {
                    "role": "system",
                    "content": SIMPLE_SUMMARY_PROMPT.format(transcript=transcript)
                }
            ]
        )
        
        summary = completion.choices[0].message.content
        print("✅ Summary complete!")
        return summary

    except Exception as e:
        print(f"❌ Error during summarization: {e}")
        return f"Error: {e}"

# --- Test this module independently ---
if __name__ == "__main__":
    print("--- Testing Summarizer Module ---")
    
    test_transcript = """
    Hi, this is the first test of Remember Me project. I'm talking to my
    daughter Sarah. She said she is coming to visit on Thursday.
    We are planning to go to the park, and she will bring the grandchildren.
    I'm very excited. I just need to remember to take my medication
    at 2pm before she arrives.
    """
    
    summary = summarize_transcript(test_transcript)
    
    print("\n--- Test Transcript ---")
    print(test_transcript)
    print("\n--- Generated Summary ---")
    print(summary)
    print("-------------------------")