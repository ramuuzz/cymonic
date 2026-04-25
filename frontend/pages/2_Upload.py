"""
Upload Page — Upload transcripts, auto-trigger extraction & sentiment.
"""
import streamlit as st
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("FASTAPI_BASE_URL", "https://cymonic-latest.onrender.com")

st.set_page_config(page_title="Upload | Meeting Hub", page_icon="📤", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .upload-zone {
        border: 2px dashed rgba(102,126,234,0.5);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        background: rgba(102,126,234,0.05);
        margin-bottom: 1.5rem;
    }

    .success-card {
        background: linear-gradient(135deg, #065f46, #064e3b);
        border: 1px solid rgba(74,222,128,0.3);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.5rem 0;
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


st.title("📤 Upload Transcripts")
st.markdown("Upload `.txt` or `.vtt` meeting transcript files for AI analysis.")

# ── Project selector ─────────────────────────────────
projects = api_get("/api/projects") or []
project_names = [p["name"] for p in projects]

col1, col2 = st.columns([3, 2])
with col1:
    mode = st.radio(
        "Project",
        ["Existing Project", "Create New"],
        horizontal=True,
    )
with col2:
    if mode == "Existing Project" and project_names:
        selected_name = st.selectbox("Select Project", project_names)
        selected_project = next(p for p in projects if p["name"] == selected_name)
        project_id = selected_project["id"]
        project_name = None
    elif mode == "Create New":
        project_name = st.text_input("New Project Name", placeholder="e.g., Q4 Strategy Meetings")
        project_id = None
    else:
        project_name = st.text_input("Project Name (first project)", placeholder="e.g., Team Standups")
        project_id = None

st.markdown("---")

# ── File uploader ────────────────────────────────────
uploaded_files = st.file_uploader(
    "Drop transcript files here",
    type=["txt", "vtt"],
    accept_multiple_files=True,
    help="Supported formats: .txt (plain text with Speaker labels) and .vtt (WebVTT captions)",
)

auto_analyze = st.checkbox("🤖 Auto-run extraction & sentiment after upload", value=True)

if uploaded_files and st.button("🚀 Upload & Process", type="primary", use_container_width=True):
    results = []
    progress = st.progress(0, text="Uploading...")

    for i, f in enumerate(uploaded_files):
        progress_pct = (i) / len(uploaded_files)
        progress.progress(progress_pct, text=f"Uploading {f.name}...")

        data = {}
        if project_id:
            data["project_id"] = project_id
        elif project_name:
            data["project_name"] = project_name

        try:
            resp = requests.post(
                f"{API_BASE}/api/transcripts/upload",
                files={"file": (f.name, f.read(), "text/plain")},
                data=data,
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            results.append(result)

            if auto_analyze:
                tid = result["id"]
                progress.progress(progress_pct + 0.3 / len(uploaded_files), text=f"Extracting insights from {f.name}...")
                try:
                    requests.post(f"{API_BASE}/api/extraction/{tid}", timeout=60)
                except:
                    pass

                progress.progress(progress_pct + 0.6 / len(uploaded_files), text=f"Analyzing sentiment for {f.name}...")
                try:
                    requests.post(f"{API_BASE}/api/sentiment/{tid}", timeout=60)
                except:
                    pass

        except Exception as e:
            st.error(f"❌ Failed to upload {f.name}: {e}")

    progress.progress(1.0, text="✅ All done!")
    time.sleep(0.5)
    progress.empty()

    if results:
        st.success(f"✅ Successfully uploaded {len(results)} file(s)!")
        st.markdown("### Upload Summary")

        for r in results:
            st.markdown(f"""
            <div class="success-card">
                <strong>📄 {r['file_name']}</strong><br/>
                🗣️ <strong>{r['speaker_count']}</strong> speakers &nbsp;|&nbsp;
                📝 <strong>{r['word_count']}</strong> words &nbsp;|&nbsp;
                📅 {r.get('meeting_date') or 'No date detected'}<br/>
                <em>{r['message']}</em>
            </div>
            """, unsafe_allow_html=True)

        st.balloons()

        st.info("💡 Head to **Meeting Detail** to view extracted insights, or **Dashboard** for an overview.")
