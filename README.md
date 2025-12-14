````markdown
# ⚖️ Legal AI Agent (Production Grade)

> **Secure, Multi-modal Legal Analysis System with Real-time Compliance & Document RAG.**

This is a modular, production-ready AI system designed to assist legal professionals. It features a microservice-style architecture (FastAPI Backend + Gradio Frontend), secure authentication, RBAC-ready auditing, and a specialized Tool-Calling Agent powered by DeepSeek (via OpenRouter) and LangChain.

---

## 🚀 Key Features

* **📄 RAG Document Analysis:** Upload PDF contracts or legal images. The system chunks, vectorizes (ChromaDB), and retrieves specific clauses for analysis.
* **🌐 Real-Time Compliance:** Checks advice against current regulations (GDPR, CCPA, Local Laws) using live web search (SerpApi).
* **🔍 Citation Validation:** Verifies if quoted case laws or statutes actually exist to prevent AI hallucinations.
* **⚖️ Clause Comparison:** Semantically compares two legal texts using Cosine Similarity to highlight differences.
* **🔒 Security First:**
    * **JWT Authentication:** Secure OAuth2 login flow.
    * **Audit Logging:** Tracks every user action (Login, Upload, Analyze) in `audit_trail.log`.
    * **Data Privacy:** Uploaded files are processed in-memory/temporarily and **securely deleted** immediately after vectorization.
    * **Strict Policies:** Enforced password strength (min 8 chars) and API rate limiting.
* **⚡ Rate Limiting:** Protected against abuse via `SlowAPI` (e.g., 10 requests/minute).

---

## 🛠️ System Architecture

The project is structured as a modular monolith for maintainability:

```text
legal_ai_system/
├── backend/                 # FastAPI Server
│   ├── engine/              # AI Engine Package
│   │   ├── agent.py         # Tool-Calling Agent & System Prompt
│   │   ├── tools.py         # Definition of RAG & Search Tools
│   │   ├── core.py          # LLM & Embedding Initialization
│   │   └── ...
│   ├── config.py            # Settings & Logging
│   ├── database.py          # SQLite User Store
│   ├── security.py          # JWT & Password Hashing
│   └── main.py              # API Entry Point
├── frontend/                # Gradio Client
│   ├── app.py               # UI Layout & Event Handlers
│   ├── client.py            # API Communication Logic
│   └── styles.py            # CSS Styling
├── requirements.txt         # Dependencies
├── test_suite.py            # Pytest Integration Tests
└── .env                     # Secrets (Not committed)
````

-----

## ⚙️ Installation

### Prerequisites

  * Python 3.10+
  * [OpenRouter API Key](https://openrouter.ai/) (for DeepSeek LLM)
  * [SerpApi Key](https://serpapi.com/) (for Real-time Search)

### 1\. Clone & Setup

```bash
# Clone the repository
git clone [https://github.com/yourusername/legal-ai-agent.git](https://github.com/yourusername/legal-ai-agent.git)
cd legal-ai-agent

# Create Virtual Environment
python -m venv venv
# Activate:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt
```

### 2\. Configure Environment

Create a `.env` file in the root directory:

```ini
OPENROUTER_API_KEY=your-key-here
SERPAPI_API_KEY=your-serpapi-key-here
SECRET_KEY=your-secure-random-string
```

-----

## 🏃‍♂️ Usage

**You must run the Backend and Frontend in separate terminals.**

### Terminal 1: Backend (Server)

Starts the FastAPI server on `http://localhost:8000`.

```bash
uvicorn backend.main:app --reload
```

*Wait for "Application startup complete"*

### Terminal 2: Frontend (UI)

Starts the Gradio interface on `http://127.0.0.1:7860`.

```bash
python -m frontend.app
```

### 🧪 Running Tests

Run the integration test suite to verify Auth, Rate Limiting, and API endpoints.

```bash
python test_suite.py
```

-----

## 🛡️ Security & Roles

  * **Registration:** New users can sign up via the UI.
  * **Password Policy:** Passwords must be at least 8 characters long.
  * **Admin Backdoor (Development Only):**
      * Username: `admin`
      * Password: `admin123!`
      * *Note: This bypasses the DB check for testing purposes.*

-----

## 🧠 AI Tools Explained

| Tool Name | Trigger Phrase | Function |
| :--- | :--- | :--- |
| **rag\_search\_tool** | "In the contract...", "What is the termination date?" | RAG lookup in uploaded file. |
| **compliance\_check\_tool** | "Is this legal in California?", "Check GDPR compliance" | Live Web Search + Analysis. |
| **clause\_comparison\_tool** | "Compare Clause A | Clause B" | Cosine Similarity analysis. |
| **citation\_validation\_tool** | "Validate case Roe v. Wade" | Verifies legal citations via Search. |

-----

## 📜 License

This project is open-source under the **MIT License**..
