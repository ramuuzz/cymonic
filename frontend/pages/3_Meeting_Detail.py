"""
Meeting Detail Page — View extracted items, edit, export, and sentiment charts.
"""
import streamlit as st
import requests
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("FASTAPI_BASE_URL", "http://13.60.67.152:8000")

st.set_page_config(page_title="Meeting Detail | Meeting Hub", page_icon="📋", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .meeting-header {
        background: linear-gradient(135deg, #1e1e30, #2a2a4a);
        border: 1px solid rgba(102,126,234,0.3);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .meeting-header h2 {
        margin-bottom: 0.5rem;
    }
    .meta-badge {
        display: inline-block;
        background: rgba(102,126,234,0.15);
        border: 1px solid rgba(102,126,234,0.3);
        border-radius: 8px;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        font-size: 0.85rem;
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


st.title("📋 Meeting Detail")

project = st.session_state.get("selected_project")
if not project:
    st.warning("⬅️ Select a project from the sidebar on the main page first.")
    st.stop()

# Transcript selector
transcripts = api_get(f"/api/transcripts/{project['id']}") or []
if not transcripts:
    st.info("No transcripts in this project yet. Go to Upload to add some.")
    st.stop()

t_names = [t["file_name"] for t in transcripts]
selected_name = st.selectbox("Select Meeting", t_names)
selected_t = next(t for t in transcripts if t["file_name"] == selected_name)
tid = selected_t["id"]

# Fetch detail
detail = api_get(f"/api/transcripts/{tid}/detail")
if not detail:
    st.error("Could not load transcript detail.")
    st.stop()

# ── Header ───────────────────────────────────────────
st.markdown(f"""
<div class="meeting-header">
    <h2>📄 {detail['file_name']}</h2>
    <span class="meta-badge">🗣️ {detail['speaker_count']} speakers</span>
    <span class="meta-badge">📝 {detail['word_count']} words</span>
    <span class="meta-badge">📅 {detail.get('meeting_date') or 'No date'}</span>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🎯 Decisions & Actions", "💬 Sentiment", "📜 Raw Transcript"])

# ── Tab 1: Decisions & Action Items ──────────────────
with tab1:
    items = api_get(f"/api/extraction/{tid}/items") or []

    if not items:
        st.info("No extracted items yet.")
        if st.button("🤖 Run Extraction", key="run_extraction", type="primary"):
            with st.spinner("Extracting decisions and action items..."):
                try:
                    r = requests.post(f"{API_BASE}/api/extraction/{tid}", timeout=60)
                    r.raise_for_status()
                    result = r.json()
                    st.success(f"✅ Extracted {result['total_count']} items!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Extraction failed: {e}")
    else:
        decisions = [i for i in items if i["type"] == "decision"]
        actions = [i for i in items if i["type"] == "action_item"]

        col1, col2 = st.columns(2)
        col1.metric("✅ Decisions", len(decisions))
        col2.metric("📋 Action Items", len(actions))

        if decisions:
            st.subheader("✅ Decisions")
            for d in decisions:
                with st.expander(f"📌 {d['description'][:80]}...", expanded=False):
                    st.write(d["description"])

        if actions:
            st.subheader("📋 Action Items")
            df = pd.DataFrame(actions)
            df_display = df[["owner", "description", "due_date"]].copy()
            df_display.columns = ["Owner", "Description", "Due Date"]
            df_display = df_display.fillna("")

            edited = st.data_editor(
                df_display,
                use_container_width=True,
                num_rows="fixed",
                key="action_items_editor",
            )

            if st.button("💾 Save Changes", key="save_actions"):
                for idx, row in edited.iterrows():
                    item_id = actions[idx]["id"]
                    try:
                        requests.put(
                            f"{API_BASE}/api/extraction/item/{item_id}",
                            json={
                                "owner": row["Owner"],
                                "description": row["Description"],
                                "due_date": row["Due Date"] if row["Due Date"] else None,
                            },
                            timeout=10,
                        )
                    except:
                        pass
                st.success("✅ Changes saved!")

        # Export buttons
        st.markdown("---")
        st.subheader("📥 Export")
        ec1, ec2, _ = st.columns([1, 1, 3])
        with ec1:
            try:
                csv_resp = requests.get(f"{API_BASE}/api/extraction/{tid}/export?format=csv", timeout=10)
                if csv_resp.ok:
                    st.download_button(
                        "⬇️ CSV",
                        data=csv_resp.content,
                        file_name=f"{detail['file_name']}_items.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
            except:
                st.button("⬇️ CSV (unavailable)", disabled=True)
        with ec2:
            try:
                pdf_resp = requests.get(f"{API_BASE}/api/extraction/{tid}/export?format=pdf", timeout=10)
                if pdf_resp.ok:
                    st.download_button(
                        "⬇️ PDF",
                        data=pdf_resp.content,
                        file_name=f"{detail['file_name']}_items.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            except:
                st.button("⬇️ PDF (unavailable)", disabled=True)

        # Re-run extraction
        if st.button("🔄 Re-run Extraction", key="rerun_extraction"):
            with st.spinner("Re-extracting..."):
                try:
                    r = requests.post(f"{API_BASE}/api/extraction/{tid}", timeout=60)
                    r.raise_for_status()
                    st.success("✅ Re-extraction complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")


# ── Tab 2: Sentiment ─────────────────────────────────
with tab2:
    sentiments = api_get(f"/api/sentiment/{tid}") or []

    if not sentiments:
        st.info("No sentiment data yet.")
        if st.button("🤖 Run Sentiment Analysis", key="run_sentiment", type="primary"):
            with st.spinner("Analyzing sentiment..."):
                try:
                    r = requests.post(f"{API_BASE}/api/sentiment/{tid}", timeout=60)
                    r.raise_for_status()
                    st.success(f"✅ Analyzed {len(r.json())} segments!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Sentiment analysis failed: {e}")
    else:
        sdf = pd.DataFrame(sentiments)

        # Summary metrics
        sc1, sc2, sc3 = st.columns(3)
        pos = len(sdf[sdf["sentiment"] == "positive"])
        neu = len(sdf[sdf["sentiment"] == "neutral"])
        neg = len(sdf[sdf["sentiment"] == "negative"])
        sc1.metric("😊 Positive", pos)
        sc2.metric("😐 Neutral", neu)
        sc3.metric("😟 Negative", neg)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Sentiment by Speaker")
            if "speaker" in sdf.columns:
                speaker_sent = sdf.groupby(["speaker", "sentiment"]).size().reset_index(name="count")
                colors = {"positive": "#4ade80", "neutral": "#60a5fa", "negative": "#f87171"}
                fig = px.bar(
                    speaker_sent, x="speaker", y="count",
                    color="sentiment", barmode="group",
                    color_discrete_map=colors,
                )
                fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter"),
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📈 Sentiment Timeline")
            score_map = {"positive": 1, "neutral": 0, "negative": -1}
            sdf["score"] = sdf["sentiment"].map(score_map)
            sdf = sdf.sort_values("segment_index")

            color_map = {1: "#4ade80", 0: "#60a5fa", -1: "#f87171"}
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=sdf["segment_index"], y=sdf["score"],
                mode="lines+markers",
                line=dict(color="#667eea", width=2),
                marker=dict(
                    color=[color_map[s] for s in sdf["score"]],
                    size=10,
                    line=dict(width=1, color="white"),
                ),
                hovertext=sdf.get("tone", ""),
            ))
            fig2.update_layout(
                template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Segment #",
                yaxis_title="Sentiment",
                yaxis=dict(tickvals=[-1, 0, 1], ticktext=["Negative", "Neutral", "Positive"]),
                font=dict(family="Inter"),
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Segments detail
        st.subheader("💬 Segment Details")
        for _, seg in sdf.iterrows():
            emoji = "😊" if seg["sentiment"] == "positive" else "😐" if seg["sentiment"] == "neutral" else "😟"
            with st.expander(f"{emoji} Segment {seg['segment_index']} — {seg.get('speaker', 'Unknown')} ({seg.get('tone', '')})"):
                st.write(seg["segment_text"])

        # Re-run
        if st.button("🔄 Re-run Sentiment Analysis", key="rerun_sentiment"):
            with st.spinner("Re-analyzing..."):
                try:
                    r = requests.post(f"{API_BASE}/api/sentiment/{tid}", timeout=60)
                    r.raise_for_status()
                    st.success("✅ Done!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

# ── Tab 3: Raw Transcript ────────────────────────────
with tab3:
    st.code(detail["raw_text"], language=None)
