# Self-Healing RAG — Phase 11: Multilingual

Phase 11 adds first-class English, Kannada, Hindi and Telugu support to both General AI Chat and Knowledge RAG.

## Added
- Auto language detection for English (`en`), Kannada (`kn`), Hindi (`hi`) and Telugu (`te`).
- Manual language selection remains available.
- Multilingual dense retrieval with `intfloat/multilingual-e5-small`.
- Hybrid retrieval remains enabled: multilingual dense vectors + BM25 sparse retrieval + Qdrant RRF fusion.
- RAG answers are instructed to respond in the selected/detected language while remaining grounded in retrieved evidence.
- General chatbot responses use the selected/detected language.
- Existing user isolation, citations, bounded self-healing and abstention are preserved.

## Important migration
The Qdrant collection is now `knowledge_chunks_multilingual_hybrid_v2`. Re-upload/reprocess knowledge documents once so they are embedded with the multilingual model.

## Run (Windows CMD)
```bat
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m backend.app.db.init_db
uvicorn backend.app.main:app --reload
```

Second CMD:
```bat
venv\Scripts\activate
streamlit run frontend/app.py
```

## Test
Upload a document and ask related questions in English, Kannada, Hindi and Telugu. Choose `Auto` to test automatic language detection. Also ask an unsupported question and verify that RAG abstains instead of inventing evidence.

## Phase 12 — Voice + OCR
- Browser microphone capture with Streamlit `audio_input`.
- Backend speech-to-text for English, Kannada, Hindi and Telugu.
- Text-to-speech endpoint for the same four languages.
- PDF OCR fallback: normal PDF extraction runs first; OCR is used only when extracted text is too sparse.
- OCR never invents missing text; empty OCR fails safely.

### Windows OCR prerequisite
Install Tesseract OCR and the `eng`, `kan`, `hin`, and `tel` language data. Ensure `tesseract.exe` is on PATH, then verify with `tesseract --version` and `tesseract --list-langs`.

## Phase 13 — Safe Browser + YouTube Control

Adds authenticated browser tools backed by Playwright: public URL opening, Google web search, YouTube search + first-result playback, and pause/resume. Browser automation uses an isolated Chrome profile under `data/browser_profile`; it does not reuse the user's normal Chrome profile, cookies, or login state. URL opening blocks localhost/private/link-local/reserved destinations.

### Windows setup
After `pip install -r requirements.txt`, ensure Google Chrome is installed. This phase launches the installed Chrome channel through Playwright. If Chrome is unavailable, install it before using Browser & YouTube.

### Test
Start FastAPI and Streamlit as usual. Open **Browser & YouTube** in the sidebar and try `Shape of You Ed Sheeran`, then Pause/Resume.

## Phase 13 natural-language action routing patch
The AI Chatbot now intercepts explicit browser/media commands before they reach the LLM. Supported examples include `Play Shape of You`, `Pause the video`, `Resume the video`, `Search Google for Python tutorials`, `Open YouTube`, and explicit public HTTP/HTTPS URLs. Other prompts continue to the normal LLM chatbot. The existing isolated Playwright browser and URL safety checks remain in force.

## Phase 14 — Testing, RAG Evaluation & Security Hardening

Adds repeatable pytest checks, an offline evidence-gate evaluation harness, HTTP security headers, request-size protection, and regression tests for SSRF/browser URL blocking, self-healing evidence checks, and multilingual language handling.

Run after installing requirements:

```bat
pytest -q
python -m evaluation.rag_eval
```

The evaluation harness intentionally runs without an LLM key. Production RAG answers still require a configured LLM provider. Browser tests do not launch Chrome.
