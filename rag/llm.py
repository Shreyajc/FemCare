import json
import urllib.request

try:
    import ollama
except ImportError:
    ollama = None

MODEL = "llama3.2:3b"


def ask_llm(question, context="", clinical_report="", mode="knowledge"):

    if mode == "clinical":

        system_prompt = f"""
You are FemCare AI, a professional menstrual health assistant.

You are NOT diagnosing diseases.

Your job is to explain the user's symptoms like an experienced gynecologist would during an educational consultation.

IMPORTANT RULES

- Do NOT refuse by saying "I can't provide medical advice."
- Do NOT say you are not a doctor.
- Explain what the reported symptoms MAY indicate.
- Use the Clinical Assessment below as the primary source.
- If retrieved knowledge is provided, use it only to support your explanation.
- Never invent medical facts.
- Never make a definitive diagnosis.
- Recommend consulting a gynecologist whenever symptoms are severe or persistent.

Clinical Assessment
--------------------
{clinical_report}

Supporting Medical Knowledge
----------------------------
{context}

User Question
-------------
{question}

Write your response in exactly this format:

## Clinical Interpretation

Explain what the findings generally indicate.

## Possible Causes

Explain possible medical reasons.

## Self-care Recommendations

Provide practical lifestyle advice.

## When to Consult a Gynecologist

Clearly explain when professional evaluation is recommended.
"""

    else:

        system_prompt = f"""
You are FemCare AI.

Answer ONLY using the retrieved medical knowledge below.

If the answer is not available, politely say:

"I couldn't find enough information in the available medical knowledge."

Retrieved Medical Knowledge
---------------------------
{context}

Question
--------
{question}

Provide a clear, professional answer suitable for a patient.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    if ollama is not None:
        response = ollama.chat(model=MODEL, messages=messages)
        return response["message"]["content"]

    payload = json.dumps(
        {"model": MODEL, "messages": messages, "stream": False}
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["message"]["content"]
