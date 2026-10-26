import os, re, uuid
from backend.app.llm.providers import gemini_chat, openai_chat, openrouter_chat
from backend.app.rag.healing import retrieve_with_healing, evidence_ok
from backend.app.core.language import resolve_language

PROVIDERS = {"openai": openai_chat, "gemini": gemini_chat, "openrouter": openrouter_chat}
def _call(messages: list[dict], preferred: str | None) -> tuple[str, str]:
    first = (preferred or os.getenv("LLM_PROVIDER", "openai")).lower()
    order = [first] + [p for p in PROVIDERS if p != first]
    errors=[]
    for name in order:
        try: return PROVIDERS[name](messages), name
        except Exception as exc: errors.append(f"{name}: {type(exc).__name__}")
    raise RuntimeError("No configured LLM provider succeeded. " + "; ".join(errors))

def answer(user_id: uuid.UUID, question: str, language: str, provider: str | None):
    language = resolve_language(question, language)
    hits, healing = retrieve_with_healing(user_id, question, 6)
    if not evidence_ok(question, hits):
        return ("I don't have enough evidence in your uploaded knowledge base to answer that question.", None, [], False, True)
    evidence=[]; citations=[]
    for i,h in enumerate(hits,1):
        text=str(h.get("text", "")).strip()
        source=str(h.get("source", "Unknown source"))
        evidence.append(f"[{i}] SOURCE: {source}\n{text}")
        citations.append({"id":i,"source":source,"document_id":str(h.get("document_id","")),
                          "chunk_index":int(h.get("chunk_index",0)),"quote":text[:280]})
    system=(f"You are a strict retrieval-grounded assistant. Reply in {language}. "
            "Use ONLY the supplied evidence. Every factual claim must be supported by citations like [1]. "
            "Never invent sources, page numbers, facts, or citations. If the evidence is insufficient, say exactly: "
            "INSUFFICIENT_EVIDENCE. Do not use outside knowledge.")
    prompt=f"QUESTION:\n{question}\n\nEVIDENCE:\n" + "\n\n".join(evidence)
    raw, used = _call([{"role":"system","content":system},{"role":"user","content":prompt}], provider)
    if "INSUFFICIENT_EVIDENCE" in raw.upper():
        return ("I don't have enough evidence in your uploaded knowledge base to answer that question.", used, [], False, True)
    ids={int(x) for x in re.findall(r"\[(\d+)\]", raw)}
    valid={c["id"] for c in citations}
    if not ids or not ids.issubset(valid):
        repair=("Rewrite the answer using ONLY the evidence below. Add at least one valid citation [n] to every factual statement. "
                "Use no citation number outside the supplied evidence. If support is insufficient output INSUFFICIENT_EVIDENCE.\n\n"
                f"QUESTION:\n{question}\n\nEVIDENCE:\n"+"\n\n".join(evidence)+f"\n\nDRAFT:\n{raw}")
        raw, used = _call([{"role":"system","content":system},{"role":"user","content":repair}], used)
        ids={int(x) for x in re.findall(r"\[(\d+)\]", raw)}
    if "INSUFFICIENT_EVIDENCE" in raw.upper() or not ids or not ids.issubset(valid):
        return ("I don't have enough evidence in your uploaded knowledge base to answer that question.", used, [], False, True)
    return raw, used, [c for c in citations if c["id"] in ids], True, False
