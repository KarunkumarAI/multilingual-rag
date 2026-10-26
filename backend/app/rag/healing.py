import re
import uuid
from dataclasses import dataclass, field

MAX_RAG_RETRIES = 2

@dataclass
class HealingTrace:
    attempts: int = 0
    repairs: list[str] = field(default_factory=list)
    failure: str | None = None

STOP = {"the","a","an","is","are","was","were","to","of","and","or","in","on","for","with","what","who","when","where","why","how","this","that","please","tell","explain"}

def terms(text: str) -> set[str]:
    return {x for x in re.findall(r"[\w-]+", text.lower()) if len(x) > 2 and x not in STOP}

def evidence_ok(question: str, hits: list[dict]) -> bool:
    if not hits:
        return False

    q = terms(question)
    evidence = terms(" ".join(
        str(h.get("text", "")) for h in hits[:8]
    ))

    # Direct lexical support
    if q and q & evidence:
        return True

    # Multilingual questions may not share literal words with
    # English evidence. Accept only sufficiently strong semantic hits.
    scores = [
        float(h.get("score", 0) or 0)
        for h in hits[:3]
    ]

    return bool(scores and max(scores) >= 0.20)
def classify(question: str, hits: list[dict]) -> str | None:
    if not hits:
        return "NO_RESULTS"
    if not evidence_ok(question, hits):
        return "WEAK_EVIDENCE"
    return None

def repair_query(question: str, attempt: int) -> str:
    cleaned = " ".join(question.strip().split())
    if attempt == 1:
        keywords = [x for x in re.findall(r"[\w-]+", cleaned) if x.lower() not in STOP]
        return " ".join(keywords) or cleaned
    # Second bounded repair: preserve original meaning but remove conversational wrappers.
    return re.sub(r"^(can you|could you|please|tell me|explain)\s+", "", cleaned, flags=re.I).strip() or cleaned

def retrieve_with_healing(user_id: uuid.UUID, question: str, limit: int = 6) -> tuple[list[dict], HealingTrace]:
    from backend.app.rag.vector_store import search
    trace = HealingTrace()
    query = question
    best: list[dict] = []
    for attempt in range(MAX_RAG_RETRIES + 1):
        trace.attempts = attempt + 1
        hits = search(user_id, query, min(limit + attempt * 2, 10))
        if len(hits) > len(best):
            best = hits
        failure = classify(question, hits)
        if failure is None:
            trace.failure = None
            return hits, trace
        trace.failure = failure
        if attempt >= MAX_RAG_RETRIES:
            break
        query = repair_query(question, attempt + 1)
        trace.repairs.append(f"{failure}: query_repair_{attempt + 1}")
    return best, trace
