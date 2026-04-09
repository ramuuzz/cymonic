import os
import json
import re
from typing import List, Dict
import numpy as np
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_client = None


# ---------------------------
# CLIENT
# ---------------------------
def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured in .env")
        _client = genai.Client(api_key=api_key)
    return _client


# ---------------------------
# ACTION ITEMS
# ---------------------------
def extract_action_items(transcript_text: str) -> Dict:
    c = _get_client()
    resp = c.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=f"Transcript:\n\n{transcript_text}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction=(
                "You are a meeting analyst. Extract ALL decisions and action items.\n"
                "Return JSON: {\"decisions\": [{\"description\": \"...\"}], "
                "\"action_items\": [{\"owner\": \"...\", \"description\": \"...\", \"due_date\": \"...\" or null}]}\n"
                "If no owner is clear, use \"Unassigned\"."
            ),
            temperature=0.1
        )
    )
    return json.loads(resp.text)


# ---------------------------
# SENTIMENT
# ---------------------------
def analyze_sentiment(segments: List[Dict]) -> List[Dict]:
    c = _get_client()
    all_results = []
    batch_size = 10

    for i in range(0, len(segments), batch_size):
        batch = segments[i : i + batch_size]
        text = "\n\n".join(
            f"Segment {j+1} (Speaker: {s.get('speaker','Unknown')}):\n{s['text']}"
            for j, s in enumerate(batch)
        )

        resp = c.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=text,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                system_instruction=(
                    "Analyze each segment's sentiment and tone.\n"
                    "Return JSON: {\"segments\": [{\"segment_index\": 1, "
                    "\"speaker\": \"...\", \"sentiment\": \"positive\"|\"neutral\"|\"negative\", "
                    "\"tone\": \"...\"}]}"
                ),
                temperature=0.1
            )
        )

        batch_result = json.loads(resp.text)
        all_results.extend(batch_result.get("segments", []))

    return all_results


# ---------------------------
# HELPERS
# ---------------------------
def _chunk_text(text: str, max_chars: int = 1500) -> List[str]:
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""

    for p in paragraphs:
        if len(current_chunk) + len(p) < max_chars:
            current_chunk += p + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def _normalize_text(text: str) -> str:
    text = re.sub(r"Team Lead\s+", "", text, flags=re.IGNORECASE)
    return text.strip()


def _cosine_similarity(vecs, query_vec):
    return np.array([
        np.dot(v, query_vec) / (np.linalg.norm(v) * np.linalg.norm(query_vec))
        for v in vecs
    ])


# ---------------------------
# CHAT WITH CONTEXT (FINAL)
# ---------------------------
def chat_with_context(
    question: str,
    transcript_texts: List[Dict],
    chat_history: List[Dict]
) -> Dict:

    c = _get_client()

    # -------- Chunking --------
    all_chunks = []
    for t in transcript_texts:
        chunks = _chunk_text(t["text"])
        for chunk in chunks:
            chunk = _normalize_text(chunk)
            if len(chunk) > 20:
                all_chunks.append({
                    "text": chunk,
                    "name": t["name"]
                })

    if not all_chunks:
        return {
            "answer": "No valid transcript data available.",
            "cited_meeting": None,
            "confidence": "Low"
        }

    # -------- Embeddings --------
    try:
        chunk_texts = [ck["text"] for ck in all_chunks]

        resp = c.models.embed_content(
            model='text-embedding-004',
            contents=chunk_texts
        )
        chunk_embeddings = np.array([e.values for e in resp.embeddings])

        q_resp = c.models.embed_content(
            model='text-embedding-004',
            contents=question
        )
        q_emb = np.array(q_resp.embeddings[0].values)

        similarities = _cosine_similarity(chunk_embeddings, q_emb)

        top_k = 5
        top_indices = similarities.argsort()[-top_k:][::-1]

        # Use top 3 for better relevance
        relevant_chunks = [all_chunks[i] for i in top_indices[:3]]

    except Exception as e:
        print(f"Embedding error: {e}")
        relevant_chunks = all_chunks[:3]

    # -------- Context --------
    context = ""
    for rc in relevant_chunks:
        context += rc["text"] + "\n\n"

    # -------- Detect WHY --------
    is_why = "why" in question.lower()

    extra_instruction = ""
    if is_why:
        extra_instruction = (
            "\nThis is a WHY question.\n"
            "- Identify the PRIMARY cause\n"
            "- Ignore unrelated issues\n"
            "- Include only relevant contributing factors\n"
            "- Explain the impact clearly\n"
        )

    # -------- Chat History --------
    contents = []
    for msg in chat_history[-10:]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["message"])]
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=question)]
        )
    )

    # -------- LLM Call --------
    try:
        resp = c.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are an intelligent meeting assistant.\n"
                    "Answer using the provided context.\n\n"

                    "Follow this structure strictly:\n"
                    "1. Direct answer (1-2 lines)\n"
                    "2. Supporting context (only relevant discussion)\n"
                    "3. Why it matters (impact)\n\n"

                    "IMPORTANT RULES:\n"
                    "- Do NOT mention excerpts, segment numbers, or sources\n"
                    "- Focus on the MOST relevant cause\n"
                    "- Ignore unrelated details\n"
                    "- Be natural and concise\n"
                    "- Do NOT include anything like (Excerpt ...)\n"
                    + extra_instruction +
                    f"\n\nCONTEXT:\n{context}"
                ),
                temperature=0.3
            )
        )

        answer = resp.text

        # HARD REMOVE excerpt artifacts
        answer = re.sub(r"\(.*?Excerpt.*?\)", "", answer, flags=re.IGNORECASE)
        answer = re.sub(r"Excerpt\s*\d+", "", answer, flags=re.IGNORECASE)

    except Exception as e:
        print(f"LLM error: {e}")
        return {
            "answer": f"API Error: {e}",
            "cited_meeting": None,
            "confidence": "Low"
        }

    # -------- Confidence --------
    if len(relevant_chunks) >= 3:
        confidence = "High"
    elif len(relevant_chunks) == 2:
        confidence = "Medium"
    else:
        confidence = "Low"

    # -------- Cited meeting --------
    cited = relevant_chunks[0]["name"] if relevant_chunks else None

    # -------- Smart Insight --------
    try:
        insight_prompt = f"Give one meaningful insight from this answer in one sentence:\n{answer}"

        insight_resp = c.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=insight_prompt
        )

        insight = insight_resp.text.strip()

    except:
        insight = "The answer highlights key decisions and their impact on the project."

    answer += f"\n\nKey Insight: {insight}"

    return {
        "answer": answer,
        "cited_meeting": cited,
        "confidence": confidence
    }