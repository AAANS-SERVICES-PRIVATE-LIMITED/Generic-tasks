# 🔧 Backend Architecture — S-Chat

The S-Chat backend is a **Python/FastAPI** server that acts as the AI brain of the application. It uses **LangGraph** to orchestrate a stateful multi-node AI pipeline, **LangChain** wrappers to talk to both local and cloud LLMs, and **Supabase** as its persistent data store.

---

## 📁 Folder Structure

```text
backend/
├── .env.example          # Required environment variable template
├── requirements.txt      # Python dependencies
└── app/
    ├── main.py           # FastAPI app entry point, CORS, router registration
    ├── config.py         # Env vars, subscription limits, default model
    ├── database.py       # Supabase client singleton
    ├── dependencies.py   # Auth middleware (get_current_user)
    ├── routers/
    │   ├── ai.py         # POST /api/ai/stream — SSE streaming endpoint
    │   ├── auth.py       # User registration and profile management
    │   ├── chat.py       # Chat thread CRUD (create, list, delete)
    │   └── documents.py  # PDF upload, chunking, embedding endpoint
    ├── schemas/
    │   ├── chat.py       # Pydantic models for chat/stream requests
    │   └── message.py    # Pydantic models for message creation
    └── services/
        ├── agent.py      # LangGraph pipeline (trim → retrieve → generate)
        ├── auth.py       # Auth business logic
        ├── chat.py       # Chat service layer (orchestrates DB calls)
        ├── db.py         # Centralized Supabase ORM (all DB queries here)
        └── embeddings.py # Local sentence-transformer embedding service
```

---

## 🧠 The LangGraph AI Pipeline

Every chat message flows through a 3-node **LangGraph** state machine defined in `services/agent.py`:

```
START → [trim_context] → [retrieve_context] → [call_model] → END
```

### Node 1: `trim_context`
Receives the full conversation history from Supabase. Uses LangChain's `trim_messages` to keep the total token count under 4,096, always preserving the `SystemMessage`. This prevents crashing models with long histories.

### Node 2: `retrieve_context` (RAG)
Checks if the current chat has any PDF document chunks stored. If yes:
1. Generates an embedding for the user's latest query
2. Runs a **cosine similarity search** (threshold: 0.3) against `table_document_chunks`
3. If similarity search finds nothing (vague queries like "tell about this"), falls back to fetching the first 6 chunks directly
4. Injects the matched chunks into the `SystemMessage` with high-priority framing

### Node 3: `call_model`
Routes execution to either `ChatOllama` (local) or `ChatGroq` (cloud) based on the selected model. Returns the AI response as a state update. The `ai.py` router uses `stream_mode="messages"` to intercept token-level chunks from only this node.

---

## 📄 PDF Upload Pipeline (`documents.py`)

When a PDF is uploaded to `/api/documents/upload`:

1. **File type validation** — Only `.pdf` accepted
2. **Save to temp disk** — `PyPDFLoader` requires a file path
3. **Word count guard** — Rejects PDFs over **10,000 words** with a clear 400 error
4. **Text chunking** — `RecursiveCharacterTextSplitter` with 500-char chunks, 50 overlap
5. **Embedding generation** — Each chunk is embedded with `all-MiniLM-L6-v2`
6. **Supabase insert** — Chunks saved to `table_document_chunks` with the `chat_id`
7. **Temp file cleanup** — Removed from disk in the `finally` block

---

## ⚡ Live Streaming (`ai.py`)

The `/api/ai/stream` endpoint uses FastAPI's `StreamingResponse`. The flow:

1. Save the user's message and resolve/create the `chat_id`
2. Fetch full history, build LangChain message objects
3. Check subscription usage limits
4. Run `agent_graph.stream(..., stream_mode="messages")`
5. **Filter** — Only yield `AIMessageChunk` tokens from the `call_model` node (prevents system prompt leaking)
6. After stream ends, save the accumulated response to the database

---

## 💾 Database Layer (`db.py`)

All Supabase interactions are centralized in `services/db.py`. Key functions:

| Function | Description |
|---|---|
| `db_save_message` | Saves a message + auto-generates its vector embedding |
| `db_search_document_chunks` | Cosine similarity RPC (`match_document_chunks`) |
| `db_get_document_chunks_sample` | Fallback: fetches first N chunks when similarity search fails |
| `db_get_monthly_message_count` | Counts user messages this month for subscription enforcement |

---

## 🔑 Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

```env
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

---

## 📦 Setup

```bash
cd backend
python -m venv venv
.\\venv\\Scripts\\activate   # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
