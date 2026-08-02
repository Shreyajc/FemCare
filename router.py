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

    # Clinical assessment

    if score >= 2 or len(numbers) >= 2:
        return "clinical"

    # General medical knowledge

    return "knowledge"