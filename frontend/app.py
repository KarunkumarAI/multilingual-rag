import re
import streamlit as st
from api_client import add_website, chatbot, conversations, delete_conversation, delete_document, documents, login, me, messages, rag_ask, register, upload_document, transcribe_audio, speak_text, browser_open, browser_search, youtube_play, browser_media

st.set_page_config(page_title="Self-Healing RAG", page_icon="🧠", layout="wide")
for k, v in {"token": None, "user": None, "mode": "Knowledge RAG", "chat": [], "conversation_id": None}.items():
    if k not in st.session_state: st.session_state[k] = v



def browser_intent(prompt: str):
    """Small deterministic router for explicit browser/media commands.
    Normal questions continue to the LLM; only clear action commands are intercepted.
    """
    text = " ".join(prompt.strip().split())
    low = text.lower()

    if re.fullmatch(r"(?:please\s+)?(?:pause|stop)\s+(?:the\s+)?(?:video|song|music|youtube)(?:\s+please)?[.!]?", low):
        return "media", "pause"
    if re.fullmatch(r"(?:please\s+)?(?:resume|continue)\s+(?:the\s+)?(?:video|song|music|youtube)(?:\s+please)?[.!]?", low):
        return "media", "resume"

    m = re.fullmatch(r"(?:please\s+)?play\s+(.+?)(?:\s+(?:on\s+)?youtube)?(?:\s+please)?[.!]?", text, flags=re.I)
    if m:
        query = m.group(1).strip()
        if query.lower().endswith(" on youtube"):
            query = query[:-11].strip()
        if query:
            return "youtube", query

    m = re.fullmatch(r"(?:please\s+)?(?:search|google|search google for)\s+(.+?)(?:\s+please)?[.!]?", text, flags=re.I)
    if m:
        query = re.sub(r"^(?:google\s+for|for)\s+", "", m.group(1), flags=re.I).strip()
        if query:
            return "search", query

    m = re.fullmatch(r"(?:please\s+)?open\s+(https?://\S+)(?:\s+please)?", text, flags=re.I)
    if m:
        return "open", m.group(1)
    if re.fullmatch(r"(?:please\s+)?open\s+youtube(?:\s+please)?[.!]?", low):
        return "open", "https://www.youtube.com"
    return None


def run_browser_intent(token, intent):
    kind, value = intent
    if kind == "youtube":
        data, err = youtube_play(token, value)
        return (f"▶ Playing **{data.get('title', value)}** on YouTube." if not err else None), err
    if kind == "media":
        _, err = browser_media(token, value)
        label = "Paused the current YouTube video." if value == "pause" else "▶ Resumed the current YouTube video."
        return (label if not err else None), err
    if kind == "search":
        data, err = browser_search(token, value)
        return (f"Opened a Google search for **{value}**." if not err else None), err
    data, err = browser_open(token, value)
    return (f"Opened **{data.get('title', value)}** in Chrome." if not err else None), err


def auth_screen():
    st.title("🧠 Self-Healing RAG")
    a, b = st.tabs(["Sign in", "Create account"])
    with a:
        with st.form("login"):
            e = st.text_input("Email"); p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in", use_container_width=True):
                token, msg = login(e, p)
                if token: st.session_state.token = token; st.session_state.user = me(token); st.rerun()
                st.error(msg)
    with b:
        with st.form("register"):
            e = st.text_input("Email", key="re"); p = st.text_input("Password", type="password", key="rp")
            c = st.text_input("Confirm password", type="password")
            if st.form_submit_button("Create account", use_container_width=True):
                if p != c: st.error("Passwords do not match.")
                else:
                    ok, msg = register(e, p); st.success(msg) if ok else st.error(msg)


def load_chat(cid):
    st.session_state.conversation_id = cid
    st.session_state.chat = [{"role": x["role"], "content": x["content"]} for x in messages(st.session_state.token, cid)]


def workspace():
    with st.sidebar:
        st.title("Self-Healing RAG"); st.caption(st.session_state.user["email"])
        st.session_state.mode = st.radio("Mode", ["Knowledge RAG", "AI Chatbot"])
        if st.button("＋ New Chat", use_container_width=True):
            st.session_state.chat = []; st.session_state.conversation_id = None; st.rerun()
        page = st.radio("Workspace", ["Chat", "Conversation History", "Documents", "Add Website", "Browser & YouTube", "Settings"])
        if st.button("Logout", use_container_width=True):
            st.session_state.token = None; st.session_state.user = None; st.rerun()
    if page == "Conversation History":
        st.header("Conversation History")
        for c in conversations(st.session_state.token):
            col1, col2 = st.columns([5, 1])
            if col1.button(c["title"] or "Untitled", key=f"o{c['id']}", use_container_width=True): load_chat(c["id"]); st.session_state.mode=c.get("mode", "AI Chatbot"); st.session_state.mode = "Knowledge RAG" if st.session_state.mode == "RAG" else "AI Chatbot"; st.rerun()
            if col2.button("Delete", key=f"d{c['id']}"): delete_conversation(st.session_state.token, c["id"]); st.rerun()
        return
    if page == "Documents":
        st.header("Documents")
        uploaded = st.file_uploader("Upload knowledge file", type=["pdf","csv","xlsx","xlsm","docx","txt","md","html","htm"])
        if uploaded and st.button("Process document", type="primary"):
            with st.spinner("Extracting and validating text..."):
                ok, result = upload_document(st.session_state.token, uploaded)
            if ok: st.success(f"{result['name']} → {result['status']}"); st.rerun()
            else: st.error(result)
        for d in documents(st.session_state.token):
            c1,c2,c3=st.columns([5,2,1]); c1.write(d["name"]); c2.write(d["status"])
            if c3.button("Delete",key=f"doc{d['id']}"): delete_document(st.session_state.token,d["id"]); st.rerun()
            if d.get("error"): st.caption(d["error"])
        return
    if page == "Add Website":
        st.header("Add Website")
        with st.form("website"):
            url=st.text_input("Public URL", placeholder="https://example.com/page")
            go=st.form_submit_button("Import website")
        if go:
            with st.spinner("Fetching and extracting website text..."): ok,result=add_website(st.session_state.token,url)
            st.success(f"{result['name']} → {result['status']}") if ok else st.error(result)
        return
    if page == "Browser & YouTube":
        st.header("Browser & YouTube")
        st.caption("Runs an isolated Chrome automation profile. It does not use your normal Chrome cookies or signed-in profile.")
        tab1, tab2, tab3 = st.tabs(["YouTube", "Web Search", "Open URL"])
        with tab1:
            q=st.text_input("Video or song", placeholder="Shape of You Ed Sheeran")
            if st.button("▶ Play on YouTube", type="primary", disabled=not q):
                with st.spinner("Opening Chrome and starting playback..."): data,err=youtube_play(st.session_state.token,q)
                st.error(err) if err else st.success(f"Playing: {data.get('title', q)}")
            c1,c2=st.columns(2)
            if c1.button("⏸ Pause"):
                _,err=browser_media(st.session_state.token,"pause"); st.error(err) if err else st.success("Paused")
            if c2.button("▶ Resume"):
                _,err=browser_media(st.session_state.token,"resume"); st.error(err) if err else st.success("Resumed")
        with tab2:
            q=st.text_input("Search the web")
            if st.button("Search", disabled=not q):
                data,err=browser_search(st.session_state.token,q); st.error(err) if err else st.success(f"Opened: {data.get('title','Google Search')}")
        with tab3:
            url=st.text_input("Public URL", placeholder="https://example.com")
            if st.button("Open in Chrome", disabled=not url):
                data,err=browser_open(st.session_state.token,url); st.error(err) if err else st.success(f"Opened: {data.get('title',url)}")
        return
    if page == "Settings":
        st.header("Settings"); st.info("Provider and language controls are available in Chat. More preferences arrive in later phases."); return
    st.header(st.session_state.mode); language = st.selectbox("Response language", ["Auto", "English", "Kannada", "Hindi", "Telugu"])
    provider = st.selectbox("LLM provider", ["openai", "gemini", "openrouter"])
    for x in st.session_state.chat:
        with st.chat_message(x["role"]): st.markdown(x["content"])
    audio = st.audio_input("🎤 Ask by voice")
    voice_prompt = None
    if audio and st.button("Transcribe voice"):
        voice_prompt, err = transcribe_audio(st.session_state.token, audio, language)
        if err: st.error(err)
    typed_prompt = st.chat_input(f"Ask in {language}...")
    prompt = typed_prompt or voice_prompt
    if prompt:
        st.session_state.chat.append({"role":"user", "content":prompt})
        if st.session_state.mode == "Knowledge RAG":
            with st.spinner("Retrieving evidence and validating citations..."):
                data, error = rag_ask(st.session_state.token, prompt, language, provider, st.session_state.conversation_id)
            if error: st.error(error)
            else:
                st.session_state.conversation_id=data["conversation_id"]
                display=data["answer"]
                if data.get("citations"):
                    display += "\n\n**Sources**\n" + "\n".join(f"- [{c['id']}] {c['source']} — chunk {c['chunk_index']}" for c in data["citations"])
                st.session_state.chat.append({"role":"assistant","content":display}); st.rerun()
        else:
            intent = browser_intent(prompt)
            if intent:
                with st.spinner("Running browser action..."):
                    answer, error = run_browser_intent(st.session_state.token, intent)
                if error: st.error(error)
                else:
                    st.session_state.chat.append({"role":"assistant", "content":answer}); st.rerun()
            else:
                answer, used, cid, error = chatbot(st.session_state.token, prompt, language, provider, st.session_state.conversation_id)
                if error: st.error(error)
                else:
                    st.session_state.conversation_id = cid; st.session_state.chat.append({"role":"assistant", "content":answer}); st.rerun()


if st.session_state.token and me(st.session_state.token): workspace()
else: st.session_state.token = None; auth_screen()
