"""
Dashboard Page — Project overview with Plotly visualizations.
"""
import streamlit as st
import requests
import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("FASTAPI_BASE_URL", "https://cymonic-latest.onrender.com")

st.set_page_config(page_title="Dashboard | Meeting Hub", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)


def api_get(path):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except:
        return None


st.title("📊 Dashboard")

project = st.session_state.get("selected_project")
if not project:
    st.warning("⬅️ Select a project from the sidebar on the main page first.")
    st.stop()

st.markdown(f"### Project: **{project['name']}**")

stats = api_get(f"/api/projects/{project['id']}/stats")
if not stats:
    st.error("Could not load project stats.")
    st.stop()

# ── Metric cards ─────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("📄 Transcripts", stats["total_transcripts"])
c2.metric("✅ Decisions", stats["total_decisions"])
c3.metric("📋 Action Items", stats["total_action_items"])
score = stats["avg_sentiment_score"]
c4.metric("💬 Avg Sentiment", f"{score:+.2f}", delta="positive" if score > 0 else "negative" if score < 0 else "neutral")

st.markdown("---")

# ── Per-transcript breakdown ─────────────────────────
transcripts = api_get(f"/api/transcripts/{project['id']}") or []
if transcripts:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Transcript Overview")
        df = pd.DataFrame(transcripts)
        df["label"] = df["file_name"].str.replace(".txt", "").str.replace(".vtt", "").str.replace("_", " ")
        fig = px.bar(
            df, x="label", y="word_count",
            color="speaker_count",
            color_continuous_scale="Viridis",
            labels={"label": "Meeting", "word_count": "Word Count", "speaker_count": "Speakers"},
            title="Word Count by Meeting",
        )
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Aggregate sentiment across all transcripts
        all_sentiments = []
        for t in transcripts:
            sents = api_get(f"/api/sentiment/{t['id']}") or []
            for s in sents:
                s["meeting"] = t["file_name"]
            all_sentiments.extend(sents)

        if all_sentiments:
            st.subheader("💬 Sentiment Distribution")
            sdf = pd.DataFrame(all_sentiments)
            counts = sdf["sentiment"].value_counts().reset_index()
            counts.columns = ["sentiment", "count"]
            colors = {"positive": "#4ade80", "neutral": "#60a5fa", "negative": "#f87171"}
            fig2 = px.pie(
                counts, values="count", names="sentiment",
                color="sentiment",
                color_discrete_map=colors,
                title="Overall Sentiment",
                hole=0.4,
            )
            fig2.update_layout(
                template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter"),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No sentiment data yet. Run sentiment analysis on your transcripts.")

    # Timeline
    if all_sentiments:
        st.subheader("📈 Sentiment Timeline")
        sdf = pd.DataFrame(all_sentiments)
        score_map = {"positive": 1, "neutral": 0, "negative": -1}
        sdf["score"] = sdf["sentiment"].map(score_map)
        sdf = sdf.sort_values("segment_index")

        fig3 = go.Figure()
        for meeting in sdf["meeting"].unique():
            mdf = sdf[sdf["meeting"] == meeting]
            fig3.add_trace(go.Scatter(
                x=mdf["segment_index"], y=mdf["score"],
                mode="lines+markers",
                name=meeting.replace(".txt", "").replace(".vtt", ""),
                line=dict(width=2),
                marker=dict(size=6),
            ))
        fig3.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Segment",
            yaxis_title="Sentiment Score",
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No transcripts uploaded yet. Go to the Upload page to add meetings.")
