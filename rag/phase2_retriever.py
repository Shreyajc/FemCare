from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "vectorstore" / "phase2_fused_index" / "index.joblib"


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
    top = scores.argsort()[::-1][:k]
    results: list[dict] = []
    for position in top:
        document = dict(bundle["documents"][int(position)])
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
