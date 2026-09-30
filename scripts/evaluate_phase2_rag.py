from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.phase2_retriever import retrieve_context


ORIGINAL_INDEX = ROOT / "vectorstore" / "phase2_original_index" / "index.joblib"
FUSED_INDEX = ROOT / "vectorstore" / "phase2_fused_index" / "index.joblib"
OUTPUT_DIR = ROOT / "report" / "phase2" / "assets"
MODEL = "llama3.2:3b"


QUESTIONS = [
    {
        "id": "O1",
        "set": "Original",
        "question": "What is the normal range for menstrual cycle length?",
        "expected": "A typical cycle is 21 to 35 days.",
        "checks": [["21"], ["35"], ["day"]],
        "source": "knowledge/medical_faq.txt - Normal menstrual cycle length",
    },
    {
        "id": "O2",
        "set": "Original",
        "question": "What is PCOS and what menstrual pattern can it cause?",
        "expected": "PCOS is a hormonal disorder that can cause irregular or absent menstrual cycles.",
        "checks": [["hormonal"], ["irregular", "absent"], ["cycle", "period"]],
        "source": "knowledge/medical_faq.txt - What is PCOS",
    },
    {
        "id": "O3",
        "set": "Original",
        "question": "What causes common menstrual cramps?",
        "expected": "Uterine contractions driven by prostaglandins commonly cause menstrual cramps.",
        "checks": [["prostaglandin"], ["contraction"], ["uter"],],
        "source": "knowledge/medical_faq.txt - Causes of menstrual cramps",
    },
    {
        "id": "O4",
        "set": "Original",
        "question": "How can high stress affect periods?",
        "expected": "High stress and cortisol can disrupt cycle hormones and cause delayed, irregular or missed periods.",
        "checks": [["stress", "cortisol"], ["delay", "irregular", "missed"], ["period", "cycle"]],
        "source": "knowledge/medical_faq.txt - Stress and periods",
    },
    {
        "id": "O5",
        "set": "Original",
        "question": "When should heavy menstrual bleeding receive medical attention?",
        "expected": "Medical review is advised when bleeding soaks protection every hour for consecutive hours or is persistent or severe.",
        "checks": [["hour"], ["medical", "doctor", "gynecologist", "healthcare"], ["heavy", "bleed", "soak"]],
        "source": "knowledge/medical_faq.txt - Heavy menstrual bleeding and warning signs",
    },
    {
        "id": "F1",
        "set": "Fused API",
        "question": "What Census population and median household income are attached to California records?",
        "expected": "California has a Census population of 39,287,377 and median household income of $99,122.",
        "checks": [["39287377", "39,287,377"], ["99122", "99,122"]],
        "source": "California state summary derived from femcare_final_cleaned.csv",
    },
    {
        "id": "F2",
        "set": "Fused API",
        "question": "What CDC obesity and physical inactivity prevalence are attached to Texas records?",
        "expected": "Texas has CDC obesity prevalence of 35.705% and physical inactivity prevalence of 27.917%.",
        "checks": [["35.705"], ["27.917"]],
        "source": "Texas state summary derived from femcare_final_cleaned.csv",
    },
    {
        "id": "F3",
        "set": "Fused API",
        "question": "How strong is the relationship between mean temperature and menstrual pain in the fused dataset?",
        "expected": "The Pearson correlation is -0.0165, which is negligible.",
        "checks": [["-0.0165", "0.0165"], ["negligible", "almost zero", "very weak", "close to zero"]],
        "source": "Phase 2 fused EDA weather and pain summary",
    },
    {
        "id": "F4",
        "set": "Fused API",
        "question": "Which has higher average menstrual pain in the fused data, California or Texas?",
        "expected": "California is higher: 5.321 compared with 4.277 for Texas.",
        "checks": [["california"], ["5.321", "5.32"], ["4.277", "4.28"]],
        "source": "California and Texas summaries derived from femcare_final_cleaned.csv",
    },
    {
        "id": "F5",
        "set": "Fused API",
        "question": "What CDC depression prevalence and median household income are attached to Massachusetts records?",
        "expected": "Massachusetts has CDC depression prevalence of 23.835% and median household income of $103,960.",
        "checks": [["23.835"], ["103960", "103,960"]],
        "source": "Massachusetts state summary derived from femcare_final_cleaned.csv",
    },
]


def ask_ollama(question: str, context: str) -> tuple[str, float]:
    prompt = f"""You are FemCare AI, an educational menstrual-health assistant.
Answer only from the supplied context. If the context does not contain the answer, reply exactly:
I couldn't find enough information in the available knowledge base.
Do not guess. Give a short answer and include the source label when possible.

CONTEXT
{context}

QUESTION
{question}
"""
    payload = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "seed": 42, "num_predict": 180},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["response"].strip(), time.perf_counter() - start


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def contains_group(text: str, alternatives: list[str]) -> bool:
    plain = normalize(text)
    compact = plain.replace(",", "")
    return any(alternative.lower() in plain or alternative.lower().replace(",", "") in compact for alternative in alternatives)


def score(question: dict, system: str, response: str) -> dict:
    refusal = "couldn't find enough information" in normalize(response)
    if question["set"] == "Fused API" and system == "Before fusion":
        return {
            "correct": False,
            "complete": False,
            "relevant": refusal,
            "hallucinated": not refusal,
        }
    matched = [contains_group(response, group) for group in question["checks"]]
    correct = all(matched)
    return {
        "correct": correct,
        "complete": correct,
        "relevant": not refusal,
        "hallucinated": refusal or not correct,
    }


def evaluate(system: str, index_path: Path) -> list[dict]:
    records: list[dict] = []
    for number, question in enumerate(QUESTIONS, start=1):
        print(f"{system}: {number}/{len(QUESTIONS)} {question['id']}", flush=True)
        context = retrieve_context(question["question"], k=5, index_path=index_path)
        response, elapsed = ask_ollama(question["question"], context)
        metrics = score(question, system, response)
        records.append(
            {
                "system": system,
                **question,
                "response": response,
                "retrieved_context": context,
                "response_time_seconds": round(elapsed, 3),
                **metrics,
            }
        )
    return records


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = evaluate("Before fusion", ORIGINAL_INDEX)
    results.extend(evaluate("After fusion", FUSED_INDEX))

    (OUTPUT_DIR / "phase2_rag_evaluation.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    frame = pd.DataFrame(results)
    frame.drop(columns=["retrieved_context"]).to_csv(
        OUTPUT_DIR / "phase2_rag_evaluation.csv", index=False
    )
    summary = (
        frame.groupby("system")
        .agg(
            questions_tested=("id", "count"),
            correct_answers=("correct", "sum"),
            complete_answers=("complete", "sum"),
            relevant_answers=("relevant", "sum"),
            hallucinated_answers=("hallucinated", "sum"),
            average_response_time_seconds=("response_time_seconds", "mean"),
        )
        .reset_index()
    )
    summary["accuracy_percent"] = 100 * summary["correct_answers"] / summary["questions_tested"]
    summary.to_csv(OUTPUT_DIR / "phase2_rag_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
