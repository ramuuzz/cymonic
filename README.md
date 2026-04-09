# 🧠 Meeting Intelligence Hub

> **AI-powered meeting transcript analysis** — automatically extract decisions, action items, sentiment, and answer questions about your meetings using Google Gemini.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.39-FF4B4B?logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash_Lite-4285F4?logo=google&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite_(default)-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📤 **Transcript Upload** | Upload `.txt` or `.vtt` meeting files with automatic parsing |
| 🤖 **AI Extraction** | Gemini extracts decisions & action items with owners and due dates |
| 📊 **Sentiment Analysis** | Per-speaker sentiment scoring with trend charts |
| 💬 **RAG Chatbot** | Ask questions across all meeting transcripts using semantic search |
| 📁 **Project Management** | Organise transcripts into projects with a dashboard per project |
| 📄 **PDF / CSV Export** | Download extracted data as PDF or CSV |
| 🔌 **Offline Mode** | Run without any API key using local VADER + TF-IDF (`AI_MODE=nlp`) |

---

## 🏗️ Project Structure

```
cymonic-2/
├── backend/                   # FastAPI application
│   ├── main.py                # App entry point, router registration
│   ├── database.py            # SQLAlchemy engine, session, Base
│   ├── models/
│   │   └── db_models.py       # ORM models (Project, Transcript, ActionItem, …)
│   ├── schemas/
│   │   └── pydantic_schemas.py# Request / response Pydantic models
│   ├── routers/
│   │   ├── transcripts.py     # CRUD — projects & transcripts
│   │   ├── extraction.py      # Action-item & decision extraction
│   │   ├── sentiment.py       # Sentiment analysis endpoints
│   │   └── chatbot.py         # RAG chatbot endpoint
│   └── services/
│       ├── gemini_service.py  # Google Gemini API (extraction, sentiment, RAG)
│       ├── parser_service.py  # .txt / .vtt transcript parser
│       └── export_service.py  # PDF & CSV export helpers
├── frontend/                  # Streamlit application
│   ├── app.py                 # Home page, sidebar, project selector
│   └── pages/
│       ├── 1_Dashboard.py     # Project-level stats & charts
│       ├── 2_Upload.py        # Transcript upload form
│       ├── 3_Meeting_Detail.py# Per-transcript extraction & sentiment
│       └── 4_Chatbot.py       # AI Q&A chatbot UI
├── .env.example               # ← copy this to .env and fill in your keys
├── requirements.txt           # All Python dependencies
└── .gitignore
```

---

## ⚡ Quick Start (Local — SQLite, no Docker)

### 1 — Prerequisites

- Python **3.11+**
- A free **Google Gemini API key** → [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

### 2 — Clone the repository

```bash
git clone https://github.com/<your-username>/cymonic-2.git
cd cymonic-2
```

### 3 — Create and activate a virtual environment

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 4 — Install dependencies

```bash
pip install -r requirements.txt
```

### 5 — Configure environment variables

```bash
# Copy the template
cp .env.example .env   # Windows: copy .env.example .env
```

Open `.env` and set **at minimum**:

```env
GEMINI_API_KEY=your_gemini_api_key_here
AI_MODE=gemini
```

> See [Environment Variables](#-environment-variables) for all available options.

### 6 — Start the backend

```bash
uvicorn backend.main:app --reload
```

The FastAPI server starts at **http://localhost:8000**.  
Interactive API docs → **http://localhost:8000/docs**

### 7 — Start the frontend (separate terminal)

```bash
streamlit run frontend/app.py
```

The Streamlit UI opens at **http://localhost:8501**.

---

## 🔑 Environment Variables

Copy `.env.example` → `.env` and populate the values below.

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | ✅ (for AI mode) | — | Google Gemini API key |

| `DATABASE_URL` | ❌ | `sqlite:///meeting_hub.db` | SQLAlchemy DB connection string |
| `FASTAPI_BASE_URL` | ❌ | `http://localhost:8000` | URL the frontend uses to reach the API |


---

## 🚀 Running in Offline / No-API Mode

Set `AI_MODE=nlp` in your `.env` to use **local VADER sentiment** and **TF-IDF extraction** — no internet or API key required. Accuracy is reduced compared to Gemini mode.

---

## 🧩 Module Overview

### Backend (`backend/`)

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI app factory, CORS middleware, router registration |
| `database.py` | SQLAlchemy engine + session factory, SQLite pragma helpers |
| `models/db_models.py` | ORM models: `Project`, `Transcript`, `ActionItem`, `SentimentSegment`, `ChatHistory` |
| `schemas/pydantic_schemas.py` | Pydantic v2 request/response schemas for all endpoints |
| `routers/transcripts.py` | `GET/POST/DELETE` routes for projects & transcript upload |
| `routers/extraction.py` | Trigger AI extraction on a transcript |
| `routers/sentiment.py` | Trigger sentiment analysis on a transcript |
| `routers/chatbot.py` | RAG chatbot — semantic search + Gemini generation |
| `services/gemini_service.py` | Gemini API wrapper — action items, sentiment, embeddings, chat |
| `services/parser_service.py` | `.txt` / `.vtt` file parsers — extracts speaker turns |
| `services/export_service.py` | PDF (fpdf2) and CSV (pandas) export helpers |

### Frontend (`frontend/`)

| Page | Path | Purpose |
|---|---|---|
| Home | `app.py` | Sidebar project selector, backend health check, stats overview |
| Dashboard | `pages/1_Dashboard.py` | Per-project charts and KPI metrics |
| Upload | `pages/2_Upload.py` | Drag-and-drop transcript upload |
| Meeting Detail | `pages/3_Meeting_Detail.py` | Extraction results, sentiment timeline, export |
| Chatbot | `pages/4_Chatbot.py` | AI Q&A chat interface |

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend health check |
| `GET` | `/api/projects` | List all projects |
| `POST` | `/api/projects` | Create a project |
| `DELETE` | `/api/projects/{id}` | Delete a project |
| `GET` | `/api/projects/{id}/stats` | Dashboard stats for a project |
| `POST` | `/api/transcripts/upload` | Upload a `.txt` / `.vtt` file |
| `GET` | `/api/transcripts/{project_id}` | List transcripts in a project |
| `GET` | `/api/transcripts/{id}/detail` | Full transcript with extracted data |
| `DELETE` | `/api/transcripts/{id}` | Delete a transcript |
| `POST` | `/api/extract/{transcript_id}` | Run AI extraction |
| `POST` | `/api/sentiment/{transcript_id}` | Run sentiment analysis |
| `POST` | `/api/chat/{project_id}` | Ask a question via the RAG chatbot |

Full interactive docs available at **http://localhost:8000/docs** when the server is running.

---

## 📋 Dependencies

All dependencies are pinned in [`requirements.txt`](./requirements.txt).

| Package | Purpose |
|---|---|
| `fastapi` | REST API framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | ORM / database layer |
| `google-genai` | Gemini API client |
| `numpy` | Cosine similarity for RAG |
| `streamlit` | Frontend UI framework |
| `plotly` | Interactive charts |
| `fpdf2` | PDF export |
| `pandas` | CSV export & data handling |
| `vaderSentiment` | Local sentiment (offline mode) |
| `scikit-learn` | TF-IDF extraction (offline mode) |



