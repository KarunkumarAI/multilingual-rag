import os
from backend.app.llm.providers import gemini_chat, openai_chat, openrouter_chat
from backend.app.core.language import resolve_language

PROVIDERS = {"openai": openai_chat, "gemini": gemini_chat, "openrouter": openrouter_chat}


def chat(message: str, language: str, provider: str | None = None) -> tuple[str, str]:
    language = resolve_language(message, language)
    system = ("You are the general AI chatbot in a multilingual assistant. "
              f"Reply in {language}. Do not claim to use uploaded documents or RAG evidence.")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": message}]
    preferred = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()
    order = [preferred] + [p for p in PROVIDERS if p != preferred]
    errors = []
    for name in order:
        try:
            return PROVIDERS[name](messages), name
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}")
    raise RuntimeError("No configured LLM provider succeeded. " + "; ".join(errors))
