"""
Meeting Intelligence Hub — Streamlit App
Main entry point with sidebar navigation and project selector.
"""
import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("FASTAPI_BASE_URL", "https://cymonic-latest.onrender.com")

st.set_page_config(
    page_title="Meeting Intelligence Hub",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        color: rgba(255,255,255,0.85);
        font-size: 1.1rem;
        margin: 0;
    }

    .stMetric > div {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1rem;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29, #302b63, #24243e);
    }
    div[data-testid="stSidebar"] .stMarkdown h1,
    div[data-testid="stSidebar"] .stMarkdown h2,
    div[data-testid="stSidebar"] .stMarkdown h3,
    div[data-testid="stSidebar"] .stMarkdown p,
    div[data-testid="stSidebar"] .stMarkdown label {
        color: #e0e0e0;
    }

    .stat-card {
        background: linear-gradient(135deg, #1e1e30, #2a2a4a);
        border: 1px solid rgba(102,126,234,0.3);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stat-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(102,126,234,0.25);
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-label {
        color: #aaa;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────
def api_get(path, **kwargs):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10, **kwargs)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


with st.sidebar:
    st.markdown("## 🧠 Meeting Hub")
    st.markdown("---")

    # Project selector
    projects = api_get("/api/projects") or []
    project_names = [p["name"] for p in projects]

    if projects:
        selected_name = st.selectbox(
            "📁 Select Project",
            project_names,
            key="project_selector",
        )
        selected_project = next(p for p in projects if p["name"] == selected_name)
        st.session_state["selected_project"] = selected_project
        st.caption(f"📝 {selected_project.get('transcript_count', 0)} transcripts")
    else:
        st.info("No projects yet. Upload a transcript to get started!")
        st.session_state["selected_project"] = None

    st.markdown("---")

    # AI mode indicator
    


# ── Main Content ─────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🧠 Meeting Intelligence Hub</h1>
    <p>AI-powered insights from your meeting transcripts — decisions, actions, sentiment & Q&A</p>
</div>
""", unsafe_allow_html=True)

# Check backend health
health = api_get("/api/health")
if health:
    st.success("✅ Backend connected")
else:
    st.error("❌ Cannot connect to backend. Make sure the FastAPI server is running on " + API_BASE)
    st.code("uvicorn backend.main:app --reload", language="bash")
    st.stop()

# Quick stats
project = st.session_state.get("selected_project")
if project:
    stats = api_get(f"/api/projects/{project['id']}/stats")
    if stats:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats['total_transcripts']}</div>
                <div class="stat-label">Transcripts</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats['total_decisions']}</div>
                <div class="stat-label">Decisions</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats['total_action_items']}</div>
                <div class="stat-label">Action Items</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            score = stats['avg_sentiment_score']
            emoji = "😊" if score > 0.2 else "😐" if score > -0.2 else "😟"
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{emoji} {score:+.2f}</div>
                <div class="stat-label">Avg Sentiment</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Recent meetings
        if stats.get("recent_meetings"):
            st.subheader("📋 Recent Meetings")
            for m in stats["recent_meetings"]:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.markdown(f"**{m['file_name']}**")
                    col2.caption(f"🗣️ {m['speaker_count']} speakers")
                    col3.caption(f"📝 {m['word_count']} words")
    else:
        st.info("Select a project from the sidebar to view stats.")
else:
    st.markdown("""
    ### 👋 Welcome!

    Get started by:
    1. **Uploading** meeting transcripts (`.txt` or `.vtt` files)
    2. **Extracting** decisions and action items
    3. **Analyzing** sentiment per speaker
    4. **Chatting** with your meeting data using AI

    Navigate using the pages in the sidebar ➡️
    """)
