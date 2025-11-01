# src/patient_assistant.py
from openai import OpenAI
from dotenv import load_dotenv
from src.database import get_all_people, get_all_medications
from datetime import datetime

load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

EMERGENCY_KEYWORDS = [
    "help", "emergency", "call 911", "can't breathe", "chest pain",
    "falling", "fell down", "hurt badly", "bleeding", "dizzy"
]


def detect_emergency(transcript: str) -> tuple[bool, str]:
    transcript_lower = transcript.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in transcript_lower:
            print(f"🚨 EMERGENCY DETECTED: '{keyword}'")
            return True, keyword
    return False, ""


def build_knowledge_base() -> str:
    knowledge = []
    try:
        people = get_all_people()
        if people:
            knowledge.append("**Family & Friends:**")
            for person in people:
                name = person.get('name')
                relationship = person.get('relationship')
                notes = person.get('notes', '')
                knowledge.append(f"- {name} ({relationship}): {notes}")
    except:
        pass

    try:
        medications = get_all_medications()
        if medications:
            knowledge.append("\n**Medications:**")
            for med in medications:
                name = med.get('name')
                time_to_take = med.get('time_to_take')
                purpose = med.get('purpose')
                knowledge.append(f"- {name}: Take at {time_to_take} for {purpose}")
    except:
        pass

    knowledge.append("\n**Home Information:**")
    knowledge.append("- The bathroom is down the hall")
    knowledge.append("- Your bedroom is at the end of the hallway")

    return "\n".join(knowledge) if knowledge else "No information available."


def answer_patient_question(question: str) -> tuple[str, bool]:
    if not client:
        return "I'm having trouble right now.", True

    print(f"🗣️ Patient asked: {question}")

    is_emergency, emergency_type = detect_emergency(question)
    if is_emergency:
        return "I'm calling your caregiver right now to help you.", True

    knowledge_base = build_knowledge_base()
    now = datetime.now()

    prompt = f"""You are a helpful assistant for a person with dementia.
Answer their question using ONLY this information: {knowledge_base}
Keep answer under 30 words. Be warm and simple.
Today is {now.strftime('%A, %B %d, %Y')}.
Question: {question}"""

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        answer = completion.choices[0].message.content.strip()
        print(f"✅ Answer: {answer}")
        return answer, False
    except Exception as e:
        print(f"❌ Error: {e}")
        return "I'm not sure about that.", False