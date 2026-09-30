import re

# -------------------------
# Greetings
# -------------------------

GREETINGS = {
    "hi",
    "hello",
    "hey",
    "hii",
    "hiya",
    "yo",
    "good morning",
    "good afternoon",
    "good evening"
}

# -------------------------
# Conversation words
# -------------------------

CASUAL = {
    "thanks",
    "thank you",
    "bye",
    "goodbye",
    "see you",
    "how are you",
    "who are you",
    "what can you do"
}

# -------------------------
# Clinical keywords
# -------------------------

SYMPTOM_WORDS = {

    "pain",
    "cramp",
    "cramps",
    "stress",
    "sleep",
    "flow",
    "bleeding",
    "period",
    "cycle",
    "pcos",
    "spotting",
    "heavy",
    "light",
    "moderate",
    "fatigue",
    "nausea",
    "vomiting",
    "dizziness",
    "fever",
    "hours",
    "/10"

}

# -------------------------
# Intent Router
# -------------------------

def route(question):

    q = question.lower().strip()

    # Greeting

    if q in GREETINGS:
        return "greeting"

    # Casual conversation

    if q in CASUAL:
        return "conversation"

    # Count symptom words

    score = sum(word in q for word in SYMPTOM_WORDS)

    # Count numbers

    numbers = re.findall(r"\d+", q)

    # Personal symptom reports need a clinical assessment. General questions
    # may mention several symptoms without describing the user's own health.
    personal_report = bool(re.search(r"\b(?:i|i'm|i've|my|me)\b", q))
    if (personal_report and (score >= 1 or numbers)) or (score >= 1 and len(numbers) >= 2):
        return "clinical"

    # General medical knowledge

    return "knowledge"
