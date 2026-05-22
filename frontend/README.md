# 🖥️ Frontend Architecture — S-Chat

The S-Chat frontend is a **React 18 + Vite** single-page application. It communicates with the FastAPI backend via a centralized HTTP client and handles real-time AI streaming via the native browser `ReadableStream` API.

---

## 📁 Folder Structure

```text
frontend/
├── .env.example          # Required environment variable template
├── index.html            # Root HTML shell
├── vite.config.js        # Vite dev server config (proxy to backend)
├── package.json
└── src/
    ├── main.jsx          # React entry point
    ├── App.jsx           # Route definitions (react-router-dom)
    ├── constants.js      # API base URL + available model registry
    ├── index.css         # Global resets
    ├── styles/           # Shared CSS design system (variables, animations)
    ├── api/
    │   ├── apiClient.js  # Core HTTP client — headers, streaming, file upload
    │   └── chatApi.js    # Chat-specific wrappers (fetch history, delete)
    ├── hooks/
    │   └── useChat.js    # Central state machine for the chat experience
    ├── pages/
    │   ├── ChatPage.jsx           # Main conversation UI (wires all components)
    │   ├── LoginPage.jsx          # Supabase Auth UI
    │   ├── SubscriptionPage.jsx   # Tier upgrade and usage display
    │   └── *.css                  # Scoped page styles
    └── components/
        ├── chat/
        │   ├── ChatInput.jsx     # Text input, model selector, file attachment
        │   ├── ChatDisplay.jsx   # Renders conversation history (markdown, images)
        │   └── Sidebar.jsx       # Chat thread list + navigation
        └── common/
            ├── Header.jsx        # Top nav bar
            ├── Subscription.jsx  # Pricing card component
            └── UsageStatus.jsx   # Monthly usage meter
```

---

## 🔁 Core Data Flow

### 1. Routing (`App.jsx`)
| Route | Component | Description |
|---|---|---|
| `/` | `ChatPage` | New chat (no ID) |
| `/chat/:chatId` | `ChatPage` | Load existing thread |
| `/login` | `LoginPage` | Auth portal |
| `/subscription` | `SubscriptionPage` | Upgrade tiers |

### 2. Model Selection (`constants.js`)
All available models are registered here. Two categories:

| Model | Provider | Vision? |
|---|---|---|
| `llama3.1` | Ollama (Local) | No |
| `phi3` | Ollama (Local) | No |
| `gemma2:2b` | Ollama (Local) | No |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Groq (Cloud) | ✅ Yes |
| `meta-llama/llama-4-maverick-17b-128e-instruct` | Groq (Cloud) | ✅ Yes |

### 3. File Attachment Logic (`useChat.js`)
When a user attaches a file before sending:

- **PDF** → fires `multipart/form-data` POST to `/api/documents/upload` first. If the upload creates a new chat (no existing `chat_id`), the new `chat_id` is captured and used for the subsequent stream request.
- **Image** → encoded to a **Base64 data URL** in the browser via `FileReader`. The base64 string is bundled directly into the stream request JSON body for multimodal processing.

### 4. Real-Time Streaming (`useChat.js` + `apiClient.js`)
1. `apiClient.stream()` opens a long-lived `POST` fetch connection
2. `response.body.getReader()` returns a `ReadableStream`
3. `TextDecoder` converts binary chunks to strings
4. A line buffer handles incomplete JSON chunks across network packets
5. Each parsed `{"text": "..."}` chunk updates the assistant message in React state incrementally — creating the "typing" effect
6. `{"chat_id": "..."}` packets update the URL without a page reload (`pushState`)
7. `{"error": "..."}` packets display inline error messages

---

## 🎨 Styling Philosophy

- **No TailwindCSS or Bootstrap** — pure Vanilla CSS
- CSS custom properties (`var(--bg-primary)`, `var(--accent-color)`) for consistent theming
- Glassmorphism effects via `backdrop-filter: blur()`
- Smooth micro-animations on hover states and message transitions
- Fully responsive from mobile (320px) to desktop (1920px)

---

## 🔑 Environment Variables

Copy `frontend/.env.example` to `frontend/.env` and fill in:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

---

## 📦 Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
