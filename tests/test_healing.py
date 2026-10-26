from backend.app.rag.healing import evidence_ok, repair_query, classify

def test_evidence_accepts_overlap():
    hits=[{"text":"Python is used for machine learning and automation."}]
    assert evidence_ok("What is Python used for?", hits)

def test_evidence_rejects_unrelated():
    hits=[{"text":"The document discusses database indexing."}]
    assert not evidence_ok("What is the candidate phone number?", hits)

def test_empty_results_classified():
    assert classify("question", []) == "NO_RESULTS"

def test_query_repair_removes_polite_prefix():
    repaired=repair_query("Please tell me Python developer skills", 1)
    assert "Python" in repaired and "skills" in repaired
