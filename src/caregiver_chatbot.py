# src/caregiver_chatbot.py
from openai import OpenAI
from dotenv import load_dotenv
from src.database import get_recent_conversations, get_all_people

load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None


def answer_caregiver_question(question: str, days_back: int = 7) -> str:
    if not client:
        return "Error: OpenAI client not initialized."

    print(f"🤔 Caregiver asked: {question}")

    conversations = get_recent_conversations(days=days_back)

    if not conversations:
        return f"I don't have any conversation records from the last {days_back} days."

    conversation_texts = []
    for i, conv in enumerate(conversations, 1):
        date = conv.get('generated_at', '').strftime('%A, %B %d at %I:%M %p') if conv.get('generated_at') else 'Unknown'
        summary = conv.get('caregiver_summary', conv.get('simple_summary', 'No summary'))
        mood = conv.get('patient_mood', 'unknown')
        concerns = conv.get('key_concerns', [])

        conv_text = f"""Conversation {i} - {date}:
- Summary: {summary}
- Patient Mood: {mood}
- Concerns: {', '.join(concerns) if concerns else 'None'}"""
        conversation_texts.append(conv_text)

    context = "\n".join(conversation_texts)

    try:
        people = get_all_people()
        people_context = "\n".join([
            f"- {p.get('name')} ({p.get('relationship')})"
            for p in people
        ]) if people else "No people profiles."
    except:
        people_context = "Error loading people."

    prompt = f"""You are helping a caregiver understand their patient's recent activity.
Answer based ONLY on this data. If info isn't here, say so.

Recent Conversations:
{context}

Known People:
{people_context}

Question: {question}"""

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        answer = completion.choices[0].message.content.strip()
        print(f"✅ Answer generated")
        return answer
    except Exception as e:
        print(f"❌ Error: {e}")
        return f"Error generating answer: {e}"