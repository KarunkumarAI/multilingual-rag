"""Small offline RAG evaluator. No LLM key is required.
Run: python -m evaluation.rag_eval
"""
from dataclasses import dataclass
from backend.app.rag.healing import evidence_ok

@dataclass
class Case:
    question: str
    evidence: list[str]
    should_answer: bool

CASES = [
    Case("What skills are mentioned?", ["Skills include Python, FastAPI and PostgreSQL."], True),
    Case("What is the phone number?", ["Skills include Python and FastAPI."], False),
    Case("Explain Qdrant", ["Qdrant is used as the vector database for retrieval."], True),
    Case("What is the salary?", [], False),
]

def run():
    correct=0
    for case in CASES:
        hits=[{"text": text} for text in case.evidence]
        predicted=evidence_ok(case.question, hits)
        correct += predicted == case.should_answer
        print(("PASS" if predicted == case.should_answer else "FAIL"), "|", case.question,
              "| expected:", case.should_answer, "predicted:", predicted)
    score=correct/len(CASES)
    print(f"\nEvidence-gate accuracy: {score:.0%} ({correct}/{len(CASES)})")
    raise SystemExit(0 if correct == len(CASES) else 1)

if __name__ == "__main__": run()
