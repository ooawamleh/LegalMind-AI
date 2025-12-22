# Legal AI Agent

A secure, full-stack AI-powered legal document analysis system with RAG (Retrieval-Augmented Generation), real-time compliance checking, and multi-modal document processing capabilities.

## 🚀 Features

### Core Capabilities
- **Multi-Modal Document Processing**: Support for PDFs, images (PNG, JPG, JPEG), and Word documents
- **RAG-Powered Analysis**: Context-aware document search and analysis using vector embeddings
- **Real-Time Compliance Checking**: Verify regulatory compliance using live web search (GDPR, CCPA, etc.)
- **Clause Comparison**: AI-powered comparison of legal clauses with similarity scoring
- **Citation Validation**: Verify legal citations and case law accuracy
- **Session Management**: Organize conversations and documents into persistent sessions
- **Streaming Responses**: Real-time AI responses for better user experience

### Security & Authentication
- JWT-based authentication with secure password hashing (bcrypt)
- Rate limiting to prevent abuse
- Audit trail logging for all user actions
- Session-isolated document access
- Automatic secure file cleanup

### User Experience
- Modern React frontend with TypeScript
- Real-time markdown rendering
- Message editing and regeneration
- Auto-generated chat titles
- File upload with visual feedback
- Mobile-responsive design

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **LLM Integration**: LangChain with OpenRouter API
- **Vector Database**: ChromaDB with HuggingFace embeddings
- **Document Processing**: Unstructured.io, LangChain loaders
- **Search**: SerpAPI for real-time web search
- **Authentication**: JWT (PyJWT) + Passlib (bcrypt)
- **Database**: SQLite with session history tracking

### Frontend
- **Framework**: React 19 with TypeScript
- **Routing**: React Router v7
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Markdown**: React-Markdown with GitHub Flavored Markdown
- **Icons**: Lucide React
- **Build Tool**: Vite (Rolldown)

## 📋 Prerequisites

- Python 3.8+
- Node.js 20.19+ or 22.12+
- OpenRouter API key (for LLM access)
- SerpAPI key (optional, for web search features)

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd legal-ai-agent
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
OPENROUTER_API_KEY=your_openrouter_api_key_here
SERPAPI_API_KEY=your_serpapi_key_here  # Optional
SECRET_KEY=your_secret_key_here  # Will auto-generate if not provided
EOF

# Run backend server
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The application will be available at:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## 🖥️ Alternative Frontend (Python / Gradio)

If you face any issues running the React frontend (such as Node version conflicts, dependency errors, or build failures), the project provides an **alternative frontend implemented purely in Python** using the **Gradio** library.

This Python-based frontend offers a simple and lightweight UI for interacting with the backend API and is especially useful for:
- Quick testing
- Development environments
- Users who prefer a Python-only stack

### 📁 Python Frontend Structure

```

├── python_frontend/
│   ├── client.py        # Backend API client
│   ├── styles.py        # UI styling and layout
│   ├── app.py           # Gradio application entry point

````

### ▶️ How to Run the Python Frontend

1. Make sure the backend server is running:
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
````

2. Activate your virtual environment (if not already active):

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required dependencies (if not already installed):

```bash
pip install gradio requests
```

4. Run the Gradio app:

```bash
python python_frontend/app.py
```

5. Open the URL shown in the terminal (usually):

```
http://127.0.0.1:7860
```

The Python frontend will connect directly to the FastAPI backend and allow you to interact with the Legal AI Agent without using React.

```

---

## ✅ Why this is good
- Clear fallback for users who struggle with React
- No confusion between frontends
- Professional OSS-style documentation
- Easy to maintain

```
---

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration and logging
│   ├── database.py            # SQLite database operations
│   ├── security.py            # Authentication and JWT handling
│   ├── schemas.py             # Pydantic models
│   ├── routers/               # API route modules
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── sessions.py       # Session management
│   │   ├── documents.py      # File upload and management
│   │   └── chat.py           # Chat and analysis endpoints
│   └── src/                   # AI/ML components
│       ├── agent.py          # LangChain agent configuration
│       ├── tools.py          # Custom AI tools
│       ├── core.py           # LLM and embeddings setup
│       ├── vector_store.py   # ChromaDB operations
│       ├── document_processor.py  # Document parsing
│       ├── system_prompt.py  # AI system instructions
│       └── context_vars.py   # Context management
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Main application component
│   │   ├── api/
│   │   │   └── client.ts     # API client with interceptors
│   │   └── components/       # React components
│   │       ├── Login.tsx
│   │       ├── Dashboard.tsx
│   │       ├── Sidebar.tsx
│   │       └── ChatArea.tsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── python_frontend/
│   ├── client.py        # Backend API client
│   ├── styles.py        # UI styling and layout
│   ├── app.py           # Gradio application entry point
├── test_suite.py              # Backend API tests
└── README.md
```

## 🔑 API Endpoints

### Authentication
- `POST /register` - Create new user account
- `POST /token` - Login and receive JWT token

### Session Management
- `GET /sessions` - List all user sessions
- `POST /sessions` - Create new session
- `PATCH /sessions/{session_id}` - Rename session
- `POST /sessions/{session_id}/auto-title` - Auto-generate title
- `DELETE /sessions/{session_id}` - Delete session
- `GET /sessions/{session_id}/history` - Get chat history

### Document Management
- `POST /upload` - Upload documents (PDF, images, Word)
- `GET /sessions/{session_id}/files` - List session files
- `DELETE /sessions/{session_id}/files/{file_id}` - Delete file

### Analysis
- `POST /analyze` - Analyze documents with streaming response

## 🤖 AI Tools

The system includes specialized AI tools:

1. **RAG Search Tool**: Searches uploaded documents with session isolation
2. **Compliance Check Tool**: Verifies regulatory compliance via web search
3. **Clause Comparison Tool**: Compares two legal clauses with similarity scoring
4. **Citation Validation Tool**: Validates legal citations and case law

## 🧪 Testing

```bash
# Run backend tests
pytest test_suite.py

# The test suite covers:
# - User registration
# - Authentication
# - Unauthorized access protection
# - Rate limiting
```

## 🔒 Security Features

- **Password Requirements**: Minimum 8 characters
- **JWT Tokens**: Secure session management with expiration
- **Rate Limiting**: 10 requests/minute on sensitive endpoints
- **Audit Logging**: All actions logged to `audit_trail.log`
- **File Isolation**: Documents tagged per session
- **Auto-cleanup**: Temporary files deleted after processing

## ⚙️ Configuration

Key configuration options in `backend/config.py`:

```python
OPENROUTER_API_KEY  # Required for LLM access
SERPAPI_API_KEY     # Optional for web search
SECRET_KEY          # JWT signing (auto-generated if not set)
UPLOAD_DIR          # Document storage location
DB_DIR              # Vector database location
ACCESS_TOKEN_EXPIRE_MINUTES  # Token expiration (default: 60)
```

## 🎨 UI Features

- **Dark/Light Theme**: Professional indigo color scheme
- **Markdown Support**: Rich text formatting with code blocks, tables
- **Message Actions**: Edit previous messages, regenerate responses
- **File Management**: Visual file cards with delete functionality
- **Session Organization**: Sidebar with rename and delete options
- **Responsive Design**: Mobile-friendly interface

## 📝 Usage Example

1. **Register/Login**: Create an account or sign in
2. **Start New Chat**: Click "New Chat" in sidebar
3. **Upload Documents**: Click upload icon to add PDFs or images
4. **Ask Questions**: Type legal questions about your documents
5. **Get AI Analysis**: Receive streaming responses with citations
6. **Manage Sessions**: Organize conversations by topic

## 🐛 Known Limitations

- Document processing may take time for large files
- Vector database builds index on first document upload
- Web search requires SerpAPI key for compliance checking
- Browser storage APIs not supported in artifacts

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Commit changes with clear messages
4. Add tests for new features
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This AI system is for informational purposes only and does not constitute legal advice. All outputs should be reviewed by qualified legal professionals. The system maintains audit logs and session isolation for security, but users are responsible for the confidentiality of their data.

## 🙏 Acknowledgments

- Built with LangChain for AI orchestration
- ChromaDB for vector storage
- Unstructured.io for document parsing
- OpenRouter for LLM access
- SerpAPI for web search capabilities
