# Meeting Intelligence Hub — Approach & Design Document

## 1. Solution Design
The Meeting Intelligence Hub is architected as a decoupled two-tier application, consisting of a RESTful backend API and a reactive frontend client. 
- **Backend (FastAPI)**: Serves as the core engine. It manages database interactions, houses the logic for parsing transcripts (supporting both `.txt` and `.vtt` formats), and orchestrates interactions with the LLM for intelligence extraction (action items, decisions, sentiment, and RAG). 
- **Frontend (Streamlit)**: Acts as the presentation layer. It consumes the REST API to provide an intuitive interface for users to upload transcripts, view analytics dashboards, and interact with the AI chatbot.
- **Database (SQLite)**: Provides persistent storage for projects, parsed transcript data, extracted action items, sentiment scoring histories, and chat history. 

The interaction flow generally involves the Frontend uploading raw files to the Backend, which parses, chunks, and persists them. Triggers then query the Gemini API to analyze the transcript content, saving the structured output locally for fast retrieval in dashboards. The RAG chatbot uses local embedding extraction and cosine similarity matching to return context-aware responses.

## 2. Tech Stack Choices & Rationale
We selected a stack optimized for rapid iteration, strong typing, robust error handling, and AI integration:

* **Python over Node.js**: Chosen because the Python ecosystem dominates the AI/ML landscape. Using Python universally allows seamless integration with both standard AI SDKs (Google GenAI) and local NLP tools.
* **FastAPI (Backend)**: Chosen for its speed, automatic Swagger UI documentation, and seamless integration with Pydantic for data validation. This ensures strongly-typed interfaces between the frontend and backend, reducing data validation errors.
* **Streamlit (Frontend)**: Selected to enable rapid prototyping of data-heavy, analytical interfaces without the overhead of building a full React frontend from scratch. It handles data visualizations (Plotly) and chat interfaces natively.
* **Google Gemini API (AI Provider)**: Chosen for its robust reasoning, large context windows, and cost-effectiveness via its generous free tier, making it ideal for processing long meeting transcripts continuously during trials.
* **SQLite (Database)**: Migrated from PostgreSQL to SQLite to dramatically simplify the local setup process for evaluators. It guarantees zero-dependency local runs on Windows, macOS, and Linux without requiring Docker. 

## 3. Future Improvements (With More Time)
If granted additional time or transitioning this to a production-ready application, we would prioritize the following improvements:

1. **Authentication & Authorization**: Implement JWT-based auth (e.g., using OAuth2) to support secure, multi-tenant access, enabling individual user accounts and team-based data segregation.
2. **Asynchronous Task Queues**: LLM calls and chunking operations are currently synchronous, which can lead to HTTP timeouts on massive transcripts (1hr+). We would implement **Celery with Redis** to offload AI extractions to background workers, streaming progress updates to the UI via WebSockets.
3. **Dedicated Vector Database**: Currently, the RAG chatbot relies on in-memory NumPy-based cosine similarity. For production scalability and handling thousands of inter-project transcripts efficiently, we would integrate a dedicated vector store like **Qdrant**, **ChromaDB**, or **pgvector**.
4. **Advanced Native Frontend**: While Streamlit is excellent for data prototyping, migrating to a custom monolithic framework like **Next.js (React)** with **Tailwind CSS** would provide finer control over responsive UI/UX, state management, and highly concurrent client sessions.
5. **Production Deployment pipeline**: Re-introduce Dockerized PostgreSQL, establish CI/CD pipelines via GitHub Actions (for linting and testing), and utilize Terraform for infrastructure-as-code deployments to AWS or GCP.
