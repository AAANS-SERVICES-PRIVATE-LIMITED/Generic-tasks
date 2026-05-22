# 🤖 S-Chat — AI Chat Application

A full-stack, production-ready AI chat application built with **React**, **FastAPI**, **LangGraph**, and **Supabase**. S-Chat is a sophisticated ChatGPT-style clone that supports hybrid AI model routing, document Q&A (RAG), real-time streaming, and multi-modal vision input.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **Hybrid AI Routing** | Switch between private local models (Ollama) and blazing-fast cloud models (Groq) |
| 📄 **Chat with PDF (RAG)** | Upload PDFs and ask questions. AI retrieves relevant context via semantic vector search |
| 🖼️ **Vision / Image Input** | Attach images to prompts. Multimodal models (Llama 4 Scout) can analyze and describe them |
| ⚡ **Live Token Streaming** | Responses stream token-by-token in real time — just like ChatGPT |
| 🧬 **Semantic Memory** | Every message is embedded into a 384-dim vector and stored in Supabase for intelligent context |
| 🔐 **Auth & Subscriptions** | Supabase Auth with per-tier monthly message limits (Free / Plus / Pro) |
| 🛡️ **Safety System Prompt** | Built-in behavioral guidelines to keep AI responses professional and safe |
| 📏 **PDF Word Limit Guard** | PDFs exceeding 10,000 words are rejected with a clear error — prevents server overload |

---

## 🛠️ Tech Stack

### Frontend
- **React 18 + Vite** — fast HMR development build
- **React Router v6** — client-side page navigation
- **Vanilla CSS** — full design control, glassmorphism, CSS variables, micro-animations
- **Native Fetch API** — streaming via `ReadableStream` + `TextDecoder`

### Backend
- **Python 3.10+ / FastAPI** — async REST API with `StreamingResponse`
- **LangGraph** — stateful AI pipeline (trim → retrieve → generate)
- **LangChain** — LLM wrappers (`ChatGroq`, `ChatOllama`) + message management
- **Sentence Transformers** (`all-MiniLM-L6-v2`) — free, local 384-dim embeddings
- **PyPDF / LangChain** — PDF ingestion and chunking
- **Groq Cloud** — ultra-fast LLM inference (Llama 4 Scout, Llama 4 Maverick)
- **Ollama** — local LLM inference (Llama 3.1, Phi-3, Gemma 2)

### Database
- **Supabase (PostgreSQL)** — user data, chat threads, messages
- **pgvector** — cosine similarity search over embeddings

---

## 📁 Project Structure

```
chatgpt_clone/
├── backend/          # FastAPI server + LangGraph AI brain
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/  # ai.py, auth.py, chat.py, documents.py
│   │   ├── services/ # agent.py, chat.py, db.py, embeddings.py
│   │   └── schemas/
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/         # React + Vite UI
    ├── src/
    │   ├── api/      # apiClient.js, chatApi.js
    │   ├── hooks/    # useChat.js
    │   ├── pages/    # ChatPage, LoginPage, SubscriptionPage
    │   └── components/
    ├── package.json
    └── .env.example
```

> See [`/backend/README.md`](./backend/README.md) and [`/frontend/README.md`](./frontend/README.md) for deep-dive architecture documentation.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **[Ollama](https://ollama.com)** installed locally (for local models)
- A **Supabase** project with `pgvector` enabled
- A **Groq** API key from [console.groq.com](https://console.groq.com)

### 1. Clone & Backend Setup
```bash
git clone https://github.com/AAANS-SERVICES-PRIVATE-LIMITED/Generic-tasks.git
git checkout gpt-clone

cd backend
python -m venv venv

# Windows
.\\venv\\Scripts\\activate
# Mac / Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # Fill in your keys
uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env   # Fill in your Supabase keys
npm run dev
```

### 3. Pull Local Models (Ollama)
```bash
ollama pull llama3.1
ollama pull phi3
ollama pull gemma2:2b
```

---

## 🔑 Environment Variables

### `backend/.env`
```env
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

### `frontend/.env`
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

---

## 🤖 Available Models

| Model | Provider | Type |
|---|---|---|
| Llama 3.1 8B | Ollama (Local) | Text |
| Phi-3 Mini | Ollama (Local) | Text |
| Gemma 2 2B | Ollama (Local) | Text |
| Llama 4 Scout 17B | Groq (Cloud) | **Text + Vision** |
| Llama 4 Maverick 17B | Groq (Cloud) | **Text + Vision** |

---

*Developed as a demonstration of modern Agentic AI capabilities using LangChain, LangGraph, and local + cloud model routing.*
