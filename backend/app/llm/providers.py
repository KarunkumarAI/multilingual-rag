import os
import requests


def _post(url: str, headers: dict, payload: dict) -> str:
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def openai_chat(messages: list[dict]) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return _post("https://api.openai.com/v1/chat/completions",
                 {"Authorization": f"Bearer {key}"},
                 {"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "messages": messages})


def openrouter_chat(messages: list[dict]) -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")
    return _post("https://openrouter.ai/api/v1/chat/completions",
                 {"Authorization": f"Bearer {key}"},
                 {"model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"), "messages": messages})


def gemini_chat(messages: list[dict]) -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    text = "\n".join(f'{m["role"]}: {m["content"]}' for m in messages)
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    r = requests.post(url, json={"contents": [{"parts": [{"text": text}]}]}, timeout=60)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]
