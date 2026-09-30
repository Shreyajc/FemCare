from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import joblib
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "vectorstore" / "phase2_fused_index" / "index.joblib"

DATA_TERMS = re.compile(
    r"\b(?:api|census|cdc|data|dataset|fused|fusion|state|states|"
    r"record|records|population|income|median|prevalence|weather|"
    r"temperature|humidity|precipitation|wind|correlation|"
    r"average|mean|compare|comparison|versus)\b",
    re.IGNORECASE,
)


@lru_cache(maxsize=4)
def load_index(path: str = str(DEFAULT_INDEX)) -> dict:
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(
            f"Knowledge base not found at {resolved}. "
            "Run embeddings/build_phase2_knowledge_base.py first."
        )
    return joblib.load(resolved)


def retrieve_documents(question: str, k: int = 5, index_path: str | Path = DEFAULT_INDEX) -> list[dict]:
    bundle = load_index(str(Path(index_path)))
    query = bundle["vectorizer"].transform([question])
    scores = cosine_similarity(query, bundle["matrix"]).ravel()
    documents = bundle["documents"]

    # A short medical question such as "What is PCOS?" otherwise matches
    # thousands of cycle rows labelled "PCOS diagnosed" before the FAQ.
    question_lower = question.lower()
    matching_state_summaries = [
        position
        for position, document in enumerate(documents)
        if document.get("record_type") == "fused_state_summary"
        and re.search(
            rf"\b{re.escape(document['record_key'].lower())}\b",
            question_lower,
        )
    ]
    mentions_state = bool(matching_state_summaries)
    if not DATA_TERMS.search(question) and not mentions_state:
        candidates = [
            position
            for position, document in enumerate(documents)
            if document.get("record_type") == "medical_knowledge"
        ]
        top = sorted(candidates, key=lambda position: scores[position], reverse=True)[:k]
    else:
        ranked = [int(position) for position in scores.argsort()[::-1] if scores[position] > 0]
        preferred = sorted(
            matching_state_summaries,
            key=lambda position: scores[position],
            reverse=True,
        )
        top = (preferred + [position for position in ranked if position not in preferred])[:k]

    results: list[dict] = []
    for position in top:
        if scores[int(position)] <= 0:
            continue
        document = dict(documents[int(position)])
        document["score"] = float(scores[int(position)])
        results.append(document)
    return results


def retrieve_context(question: str, k: int = 5, index_path: str | Path = DEFAULT_INDEX) -> str:
    blocks = []
    for document in retrieve_documents(question, k=k, index_path=index_path):
        source = document.get("source", "unknown source")
        record_key = document.get("record_key")
        label = f"Source: {source}"
        if record_key:
            label += f" | Record: {record_key}"
        blocks.append(f"{label}\n{document['text']}")
    return "\n\n".join(blocks)
