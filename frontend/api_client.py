import requests

API_URL = "http://127.0.0.1:8000"


def headers(token): return {"Authorization": f"Bearer {token}"}


def register(email, password):
    r = requests.post(f"{API_URL}/auth/register", json={"email": email, "password": password}, timeout=15)
    return (True, "Account created. You can now sign in.") if r.ok else (False, r.json().get("detail", "Registration failed"))


def login(email, password):
    r = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password}, timeout=15)
    return (r.json()["access_token"], "Signed in") if r.ok else (None, r.json().get("detail", "Login failed"))


def me(token):
    r = requests.get(f"{API_URL}/auth/me", headers=headers(token), timeout=15)
    return r.json() if r.ok else None


def chatbot(token, message, language, provider, conversation_id=None):
    body = {"message": message, "language": language, "provider": provider, "conversation_id": conversation_id}
    r = requests.post(f"{API_URL}/chatbot/message", json=body, headers=headers(token), timeout=75)
    if r.ok:
        d = r.json(); return d["answer"], d["provider"], d["conversation_id"], None
    try: detail = r.json().get("detail", "Chat request failed")
    except ValueError: detail = "Chat request failed"
    return None, None, conversation_id, detail


def conversations(token):
    r = requests.get(f"{API_URL}/conversations", headers=headers(token), timeout=15)
    return r.json() if r.ok else []


def messages(token, cid):
    r = requests.get(f"{API_URL}/conversations/{cid}/messages", headers=headers(token), timeout=15)
    return r.json() if r.ok else []


def delete_conversation(token, cid):
    return requests.delete(f"{API_URL}/conversations/{cid}", headers=headers(token), timeout=15).ok


def documents(token):
    r = requests.get(f"{API_URL}/documents", headers=headers(token), timeout=15)
    return r.json() if r.ok else []


def upload_document(token, uploaded):
    r = requests.post(f"{API_URL}/documents/upload", files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}, headers=headers(token), timeout=60)
    try: data = r.json()
    except ValueError: data = {}
    return r.ok, data if r.ok else data.get("detail", "Upload failed")


def add_website(token, url):
    r = requests.post(f"{API_URL}/documents/url", json={"url": url}, headers=headers(token), timeout=30)
    try: data = r.json()
    except ValueError: data = {}
    return r.ok, data if r.ok else data.get("detail", "Website import failed")


def delete_document(token, did):
    return requests.delete(f"{API_URL}/documents/{did}", headers=headers(token), timeout=15).ok


def rag_ask(token, question, language, provider, conversation_id=None):
    body={"question":question,"language":language,"provider":provider,"conversation_id":conversation_id}

    print("RAG QUESTION:", repr(question))
    print("RAG LANGUAGE:", repr(language))
    print("RAG PROVIDER:", repr(provider))

    r=requests.post(
        f"{API_URL}/rag/ask",
        json=body,
        headers=headers(token),
        timeout=90
    )

    print("RAG STATUS:", r.status_code)
    print("RAG RESPONSE:", r.text)

    try:
        data=r.json()
    except ValueError:
        data={}

    return (data, None) if r.ok else (None, data.get("detail","RAG request failed"))
    try: data=r.json()
    except ValueError: data={}
    return (data, None) if r.ok else (None, data.get("detail","RAG request failed"))


def transcribe_audio(token, audio, language):
    files={"file": ("voice.wav", audio.getvalue(), "audio/wav")}
    r=requests.post(f"{API_URL}/voice/transcribe",params={"language":language},files=files,headers=headers(token),timeout=60)
    try: data=r.json()
    except ValueError: data={}
    return (data.get("text"),None) if r.ok else (None,data.get("detail","Transcription failed"))

def speak_text(token,text,language):
    r=requests.post(f"{API_URL}/voice/speak",json={"text":text,"language":language},headers=headers(token),timeout=60)
    return (r.content,None) if r.ok else (None,"Speech synthesis failed")


def browser_open(token, url):
    r=requests.post(f"{API_URL}/browser/open",json={"url":url},headers=headers(token),timeout=45)
    try: data=r.json()
    except ValueError: data={}
    return (data,None) if r.ok else (None,data.get("detail","Browser open failed"))


def browser_search(token, query):
    r=requests.post(f"{API_URL}/browser/search",params={"q":query},headers=headers(token),timeout=45)
    try: data=r.json()
    except ValueError: data={}
    return (data,None) if r.ok else (None,data.get("detail","Web search failed"))


def youtube_play(token, query):
    r=requests.post(f"{API_URL}/browser/youtube/play",json={"query":query},headers=headers(token),timeout=60)
    try: data=r.json()
    except ValueError: data={}
    return (data,None) if r.ok else (None,data.get("detail","YouTube playback failed"))


def browser_media(token, action):
    r=requests.post(f"{API_URL}/browser/media",json={"action":action},headers=headers(token),timeout=30)
    try: data=r.json()
    except ValueError: data={}
    return (data,None) if r.ok else (None,data.get("detail",f"Could not {action}"))
