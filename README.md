# ⚖️ Legal AI Agent (Full-Stack)

> **A Secure, Modular Legal Analysis Platform with Real-time RAG & Compliance Checking.**

Legal AI Agent is a robust document analysis system designed for legal professionals. It replaces the traditional monolithic script with a modern **Microservices-ready architecture**, featuring a responsive **React + TypeScript** frontend and a modular **FastAPI** backend. It leverages **LangChain** agents to perform grounded contract analysis, regulatory compliance checks, and citation validation.

-----

## 🚀 Key Features

  * **🧠 Advanced RAG Analysis:**
      * **Multi-File Support:** Upload and analyze multiple PDFs, Word docs, or images simultaneously.
      * **Context Isolation:** Documents are vector-indexed (ChromaDB) specifically for the active session and do not bleed into other chats.
  * **💬 Intelligent Chat System:**
      * **Smart Auto-Titling:** Deterministic algorithms automatically rename chats based on the context of the first message (e.g., "Contract Review" vs "General Discussion").
      * **Persistent History:** Resume past conversations instantly with full context retention.
      * **Welcome Guide:** Onboarding assistant to guide new users.
  * **📂 Visual File Management:**
      * **File Cards:** Interactive UI to view and delete uploaded documents from the AI's context.
      * **Context Control:** Removing a file card instantly wipes its vector embeddings.
  * **🌐 Real-Time Compliance:** Integrated tools to check current laws (GDPR, CCPA) via live web search (SerpApi).
  * **🔒 Enterprise-Grade Security:**
      * **Ephemeral Secrets:** Server generates a new `SECRET_KEY` on every restart, automatically invalidating old tokens.
      * **RBAC-Ready Auth:** JWT-based authentication with secure Bcrypt password hashing.
      * **Audit Logging:** Detailed `audit_trail.log` tracking every login, upload, and analysis request.

-----

## 🛠️ System Architecture

The system has been refactored from a monolith into a clean, modular structure:

```text
legal-ai-agent/
├── backend/                  # Python API (FastAPI)
│   ├── main.py               # Application Entry Point
│   ├── config.py             # Configuration & Ephemeral Key Gen
│   ├── database.py           # SQLite & ChromaDB Logic
│   ├── routers/              # Modular API Routes
│   │   ├── auth.py           # Login & Registration
│   │   ├── sessions.py       # Chat CRUD & Auto-Titling
│   │   ├── documents.py      # Uploads & File Management
│   │   └── chat.py           # Streaming Analysis Endpoint
│   └── src/                  # Core AI Logic
│       ├── agent.py          # LangChain Tool-Calling Agent
│       ├── tools.py          # RAG, Search, & Comparison Tools
│       └── document_processor.py # Unstructured & OCR Pipelines
│
└── frontend/                 # Client (React + Vite)
    ├── src/
    │   ├── api/
    │   │   └── client.ts     # Centralized Axios Client
    │   ├── components/
    │   │   ├── Dashboard.tsx # Main Layout
    │   │   ├── Sidebar.tsx   # Session Management
    │   │   ├── ChatArea.tsx  # Message Stream & File Cards
    │   │   └── Login.tsx     # Auth UI
    │   └── App.tsx           # Routing & Guards
    └── package.json
```

-----

## ⚙️ Installation & Setup

### Prerequisites

  * **Backend:** Python 3.10+
  * **Frontend:** Node.js 18+ & npm
  * **API Keys:** OpenRouter (LLM) & SerpApi (Optional for search)

### 1\. Backend Setup

```bash
cd backend

# Create & Activate Virtual Environment
python -m venv venv
# Windows: venv\Scripts\activate  |  Mac/Linux: source venv/bin/activate

# Install Python Dependencies
pip install -r ../requirements.txt

# Create .env file
echo "OPENROUTER_API_KEY=your_key_here" > .env
echo "SERPAPI_API_KEY=your_key_here" >> .env
# Note: SECRET_KEY is auto-generated on startup for security
```

### 2\. Frontend Setup

```bash
cd frontend

# Install Node Dependencies
npm install

# Start Development Server
npm run dev
```

-----

## 🏃‍♂️ Usage

**You must run both servers simultaneously.**

1.  **Start Backend:**

    ```bash
    # In Terminal 1 (root folder)
    uvicorn backend.main:app --reload --port 8000
    ```

2.  **Start Frontend:**

    ```bash
    # In Terminal 2 (frontend folder)
    npm run dev
    ```

3.  **Access the App:**

      * Open `http://localhost:5173` in your browser.
      * **Register:** Create a new account.
      * **Login:** Access the dashboard.

-----

## 🧠 AI Capabilities

The agent is equipped with specific tools it chooses dynamically:

| Tool Name | Functionality |
| :--- | :--- |
| **`rag_search_tool`** | Retrieves specific clauses from your uploaded PDF/Word docs. |
| **`compliance_check_tool`** | Google searches current regulations to verify legality. |
| **`clause_comparison_tool`** | Calculates Cosine Similarity between two text inputs. |
| **`citation_validation_tool`** | Validates if a cited case law actually exists. |

-----

## 🛡️ Security Protocols

  * **Session Expiry:** Access tokens expire every 60 minutes.
  * **Force Re-Auth:** Restarting the backend server invalidates all active sessions immediately (via Ephemeral Secret Keys).
  * **Data Hygiene:** Uploaded files are processed securely; metadata allows precise deletion from the vector store when the user removes a file card.

-----

## 📜 License

This project is licensed under the **MIT License**.