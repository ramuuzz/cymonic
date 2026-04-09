"""
Chatbot Page — AI Q&A over meeting transcripts.
"""
import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("FASTAPI_BASE_URL", "http://13.60.67.152:8000")

st.set_page_config(page_title="Chatbot | Meeting Hub", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .citation-badge {
        display: inline-block;
        background: rgba(102,126,234,0.15);
        border: 1px solid rgba(102,126,234,0.3);
        border-radius: 6px;
        padding: 0.2rem 0.6rem;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def api_get(path):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except:
        return None


st.title("🤖 Meeting Chatbot")
st.markdown("Ask questions about your meetings — the AI will search through all transcripts and cite its sources.")

project = st.session_state.get("selected_project")
if not project:
    st.warning("⬅️ Select a project from the sidebar on the main page first.")
    st.stop()

st.caption(f"💬 Chatting about project: **{project['name']}**")

# ── Load chat history ────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Load from DB
history = api_get(f"/api/chat/{project['id']}/history") or []
if history and not st.session_state.chat_messages:
    st.session_state.chat_messages = [
        {"role": h["role"], "content": h["message"]}
        for h in history
    ]

# ── Clear history button ─────────────────────────────
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("🗑️ Clear History", use_container_width=True):
        try:
            requests.delete(f"{API_BASE}/api/chat/{project['id']}/history", timeout=10)
        except:
            pass
        st.session_state.chat_messages = []
        st.rerun()

# ── Render chat messages ─────────────────────────────
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("cited_meeting"):
            st.markdown(
                f'<span class="citation-badge">📌 Source: {msg["cited_meeting"]}</span>',
                unsafe_allow_html=True,
            )

# ── Chat input ───────────────────────────────────────
if prompt := st.chat_input("Ask about your meetings..."):
    # Add user message
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/api/chat/{project['id']}",
                    json={"message": prompt},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data["message"]
                cited = data.get("cited_meeting_name")

                st.markdown(answer)
                if cited:
                    st.markdown(
                        f'<span class="citation-badge">📌 Source: {cited}</span>',
                        unsafe_allow_html=True,
                    )

                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": answer,
                    "cited_meeting": cited,
                })
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {e}"
                st.error(error_msg)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })

# ── Suggested questions ──────────────────────────────
if not st.session_state.chat_messages:
    st.markdown("### 💡 Try asking:")
    suggestions = [
        "What were the main decisions made?",
        "Who has the most action items?",
        "What was the overall sentiment of the meetings?",
        "Summarize the key discussion points",
        "What deadlines were mentioned?",
    ]
    cols = st.columns(len(suggestions))
    for i, (col, q) in enumerate(zip(cols, suggestions)):
        with col:
            if st.button(q, key=f"suggest_{i}", use_container_width=True):
                st.session_state.chat_messages.append({"role": "user", "content": q})
                st.rerun()
