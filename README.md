# 🏛️ BPIE AI Policy Agent

An enterprise-ready, production-grade **AI Policy Agent** for **Bishnupur Public Institute of Engineering (BPIE)** (Bishnupur, Bankura).

Built with a **Flask** backend (deployable on **Render**), **Streamlit** frontend (deployable on **Streamlit Cloud**), **Neon PostgreSQL** for persistent storage, **Qdrant Vector Database**, **Groq Free API** (`llama-3.3-70b-versatile` & `whisper-large-v3`), **FastEmbed** zero-cost embeddings, and **FlashRank** cross-encoder reranking.

---

## 🌟 Key Features

- **Domain-Restricted Authentication & RBAC**:
  - Registration and login strictly validated for institutional emails: `*@bpie.ac.in`.
  - Secure JWT authentication with 7-day token expiration.
  - Role-Based Access Control (**RBAC**):
    - **Admin (`admin`)**: Upload college policy PDFs, inspect chunk index counts, delete documents, and purge vector collections.
    - **Student/Staff (`student`)**: Interactive chat, policy querying, citation inspection, voice assistant.
- **Production-Grade RAG (Retrieval-Augmented Generation)**:
  - **Free FastEmbed Dense Embeddings** (`BAAI/bge-small-en-v1.5`): High-accuracy 384-dimensional vectors running on CPU with ONNX (zero API cost, memory-efficient for Render 512MB RAM tier).
  - **Qdrant Vector Database**: Supports Qdrant Cloud or local disk fallback.
  - **Cross-Encoder Reranking via FlashRank**: Reranks top 12 retrieved candidates down to top 4 most pertinent chunks, preventing hallucinations and boosting answer precision.
  - **Strict Grounding & Anti-Hallucination Guardrail**: The agent answers exclusively from official institute policies and explicitly cites document name and page numbers.
- **Modern Chat Application**:
  - Dynamic **Chat Sessions**: Create new sessions, switch conversations, delete single sessions, or clear all chat history.
  - Real-time **Policy Citations Expander**: Inspect exact policy titles, page numbers, and quoted snippets for every response.
  - **Multi-Language Support**: Answers fluently in **English**, **Bengali (বাংলা)**, and **Hindi (हिंदी)**.
  - **Voice Assistant**:
    - **Speech-to-Text**: Groq Whisper Large v3 for voice queries.
    - **Text-to-Speech**: Multi-lingual audio synthesis via gTTS with inline audio playback.
  - Clean, responsive UI with customized styling.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Client["Streamlit Frontend (Cloud / Local)"]
        UI["User / Admin UI"]
        VoiceIn["Mic Voice Input (Audio)"]
        ChatHist["Sessions & Chat History"]
    end

    subgraph Backend["Flask REST API (Render)"]
        Auth["JWT Auth & @bpie.ac.in Validator"]
        STT["Groq Whisper Large v3 (STT)"]
        TTS["gTTS Audio Synthesizer"]
        AdminSvc["Admin PDF Ingestion & Chunker"]
        RAG["Production RAG Pipeline"]
    end

    subgraph Storage["Persistent & Vector Storage"]
        Neon["Neon PostgreSQL (Users, Sessions, History)"]
        Qdrant["Qdrant Vector DB (Policy Chunks)"]
    end

    subgraph AI["AI Models (Free Tier)"]
        FastEmbed["FastEmbed (BGE-Small-EN-v1.5)"]
        FlashRank["FlashRank Cross-Encoder Reranker"]
        GroqLLM["Groq Llama 3.3 70B Versatile"]
    end

    UI -->|HTTP / Bearer JWT| Auth
    VoiceIn -->|Audio WAV| STT
    STT --> UI
    AdminSvc -->|Page Text Chunks| FastEmbed
    FastEmbed -->|384-d Vectors| Qdrant
    UI -->|Ask Question| RAG
    RAG --> FastEmbed
    FastEmbed -->|Query Vector| Qdrant
    Qdrant -->|Top 12 Candidates| FlashRank
    FlashRank -->|Top 4 Reranked| GroqLLM
    GroqLLM -->|Answer + Citations| RAG
    RAG --> TTS
    RAG --> Neon
    RAG --> UI
```

---

## 📂 Project Directory Structure

```
BPIE-Policy-Agent/
├── backend/
│   ├── app.py                     # Flask application entry point
│   ├── config.py                  # Environment settings & fallbacks
│   ├── extensions.py              # SQLAlchemy & CORS setup
│   ├── requirements.txt           # Backend production dependencies
│   ├── Procfile                   # Render deployment process definition
│   ├── render.yaml                # Render Blueprint infrastructure specification
│   ├── models/
│   │   ├── user.py                # User model with role ('admin' / 'student')
│   │   ├── chat.py                # ChatSession & ChatMessage with citations
│   │   └── document.py            # PolicyDocument metadata model
│   ├── routes/
│   │   ├── auth_routes.py         # Login, Register (@bpie.ac.in), /me
│   │   ├── chat_routes.py         # Sessions, history, RAG querying, session deletion
│   │   ├── admin_routes.py        # PDF upload, document list, Qdrant deletion (RBAC)
│   │   └── voice_routes.py        # Groq Whisper transcription & gTTS speech synthesis
│   ├── services/
│   │   ├── auth_service.py        # JWT generation & decorators (@token_required, @admin_required)
│   │   ├── rag_service.py         # Qdrant + FastEmbed + FlashRank + Groq RAG pipeline
│   │   ├── pdf_service.py         # PDF page extraction & recursive chunking
│   │   └── voice_service.py       # Whisper API & text-to-speech engine
│   └── utils/
│       ├── validators.py          # Email regex validator for @bpie.ac.in
│       └── init_db.py             # Database table creator & seed admin script
├── frontend/
│   ├── app.py                     # Streamlit main entry point
│   ├── api_client.py              # Centralized HTTP client communicating with backend
│   ├── requirements.txt           # Frontend dependencies
│   ├── .streamlit/
│   │   └── config.toml            # Theme, server, and upload settings
│   └── components/
│       ├── auth_view.py           # Login & Registration screens
│       ├── sidebar.py             # Session switcher, clear chats, language, voice toggle
│       ├── chat_view.py           # Message history, citations expander, mic input
│       └── admin_view.py          # Admin PDF uploader & document management
├── sample_policies/
│   ├── bpie_academic_regulations.txt   # Official sample rules text
│   └── bpie_academic_regulations.pdf   # Valid sample PDF ready for upload testing
├── .env.example                   # Full environment variables template
├── requirements.txt               # Combined root dependencies
└── README.md                      # Complete documentation & deployment guide
```

---

## ⚙️ Prerequisites & Free Cloud Accounts

1. **Python 3.10 or 3.11** installed.
2. **Groq Cloud API Key** (100% Free):
   - Sign up at [https://console.groq.com/keys](https://console.groq.com/keys) and generate an API key (`gsk_...`).
3. **Neon PostgreSQL Database** (Free Serverless):
   - Create a free database at [https://console.neon.tech](https://console.neon.tech).
   - Copy the connection string (e.g. `postgresql://.../neondb?sslmode=require`).
4. **Qdrant Vector Database** (Free Cloud Cluster):
   - Create a free 1GB cluster at [https://cloud.qdrant.io](https://cloud.qdrant.io).
   - Copy your Cluster URL (`https://xyz.aws.cloud.qdrant.io:6333`) and API Key.
   - *(Optional: If left blank, the backend automatically uses persistent local storage in `backend/qdrant_storage`)*.

---

## 🚀 Local Quickstart Guide

### 1. Clone & Set Up Environment
```bash
cd BPIE-Policy-Agent
cp .env.example .env
```
Edit `.env` and fill in your keys:
```env
GROQ_API_KEY=gsk_your_groq_api_key
DATABASE_URL=postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key
ALLOWED_EMAIL_DOMAIN=@bpie.ac.in
ADMIN_EMAILS=admin@bpie.ac.in
```

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install all packages
pip install -r requirements.txt
```

### 3. Initialize Database & Create Initial Admin
```bash
python backend/utils/init_db.py
```
> This automatically verifies Neon PostgreSQL tables and creates the default administrator:
> - **Email**: `admin@bpie.ac.in`
> - **Password**: `AdminBpie@2026`

### 4. Run the Backend (Flask)
```bash
cd backend
python app.py
```
The Flask API runs at `http://localhost:5000`. You can verify health at `http://localhost:5000/api/health`.

### 5. Run the Frontend (Streamlit)
Open a second terminal window:
```bash
# Activate venv
venv\Scripts\activate

# Run Streamlit
streamlit run frontend/app.py
```
Your browser will open `http://localhost:8501`.

---

## 🚢 Production Deployment Guide

### Deploying Backend to Render

1. Push your repository to **GitHub**.
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **New +** -> **Web Service**.
4. Connect your GitHub repository.
5. Configure the service:
   - **Name**: `bpie-policy-agent-backend`
   - **Environment**: `Python 3`
   - **Root Directory**: Leave blank or set `backend`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `gunicorn --chdir backend app:app --workers 2 --timeout 120`
6. Add Environment Variables in Render:
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | Your Neon Postgres connection string |
   | `GROQ_API_KEY` | Your Groq API key |
   | `QDRANT_URL` | Your Qdrant Cloud URL |
   | `QDRANT_API_KEY` | Your Qdrant API Key |
   | `SECRET_KEY` | A long random secret string |
   | `ALLOWED_EMAIL_DOMAIN` | `@bpie.ac.in` |
   | `ADMIN_EMAILS` | `admin@bpie.ac.in` |
7. Click **Deploy Web Service**. Render provides a live URL: `https://bpie-policy-agent-backend.onrender.com`.

---

### Deploying Frontend to Streamlit Community Cloud

1. Log in to [Streamlit Community Cloud](https://share.streamlit.io).
2. Click **New app**.
3. Select your GitHub repository, branch (`main`), and set:
   - **Main file path**: `frontend/app.py`
4. Expand **Advanced Settings** -> **Secrets** and add:
   ```toml
   BACKEND_URL = "https://bpie-policy-agent-backend.onrender.com"
   ```
5. Click **Deploy!**. Streamlit will deploy your interactive policy app with a public URL.

---

## 🧪 Testing the Complete Workflow

1. **Sign In as Admin**:
   - Go to the Streamlit app.
   - Login with `admin@bpie.ac.in` and password `AdminBpie@2026`.
2. **Upload Policy PDF**:
   - In the sidebar, select **📑 Policy Docs Manager (Admin)**.
   - Upload `sample_policies/bpie_academic_regulations.pdf`.
   - Click **Upload & Index to Vector DB**.
   - Notice that chunks are extracted and stored in Qdrant!
3. **Switch to Policy Chat**:
   - In sidebar, switch to **💬 Chat with Policy Agent**.
   - Ask: *"What is the minimum attendance requirement for semester exams?"*
   - Observe the precise answer citing **Chapter 1, Page 1** with verbatim rule references.
4. **Test Multi-Language**:
   - Change response language in sidebar to **বাংলা (Bengali)** or **हिंदी (Hindi)**.
   - Ask: *"হোস্টেল কার্ফিউ এর নিয়ম কি?"* or *"होस्टल के नियम क्या हैं?"*
   - Observe the agent answering in your chosen language while maintaining official citations.
5. **Test Voice Assistant**:
   - Click **🎙️ Speak your question (Voice Input Assistant)**.
   - Speak your question; Groq Whisper Large v3 will transcribe it in seconds and query the agent.
   - Turn on **Enable Audio Voice Response** in sidebar to listen to the synthesized speech.
6. **Student Role & Domain Enforcement**:
   - Log out. Try to register with `test@gmail.com` -> Notice the strict rejection.
   - Register with `student.john@bpie.ac.in`. Notice they are granted `student` role and do not have access to document deletion or PDF upload.

---

## 🔒 Security Best Practices

- Passwords hashed using **pbkdf2:sha256** / bcrypt via Werkzeug.
- Authentication tokens signed using **HS256 JWT** with expiration.
- Input file sanitization prevents directory traversal attacks.
- Admin endpoints protected by `@admin_required` server-side middleware.
- Grounded RAG system prompt rejects off-topic queries or hallucinated answers.
