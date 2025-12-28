# LegalMind-AI

A secure, full-stack AI-powered legal document analysis system with RAG (Retrieval-Augmented Generation), real-time compliance checking, and multi-modal document processing capabilities.

## 🚀 Features

### Core Capabilities
- **Multi-Modal Document Processing**: Support for PDFs, images (PNG, JPG, JPEG), and Word documents
- **RAG-Powered Analysis**: Context-aware document search and analysis using vector embeddings
- **Real-Time Compliance Checking**: Verify regulatory compliance using live web search (GDPR, CCPA, etc.)
- **Clause Comparison**: AI-powered comparison of legal clauses with similarity scoring
- **Citation Validation**: Verify legal citations and case law accuracy
- **Session Management**: Organize conversations and documents into persistent sessions
- **Streaming Responses**: Real-time AI responses using FastAPI StreamingResponse and native Fetch API

### Security & Authentication
- JWT-based authentication with secure password hashing (bcrypt)
- Rate limiting on sensitive endpoints (10 requests/minute on `/upload` and `/analyze`)
- Audit trail logging for all user actions
- Session-isolated document access using ChromaDB metadata filtering
- Automatic secure file cleanup
- Token validation with automatic redirect on expiry

### User Experience
- Modern React frontend with TypeScript and component-based architecture
- Real-time markdown rendering with GitHub Flavored Markdown
- Message editing and regeneration
- **Welcome Screen**: Friendly AI greeting shown on new chats
- **Smart Auto-Titles**: Generated from first query words or uploaded filename (no LLM cost)
- File upload with visual feedback and per-session file cards
- Mobile-responsive design with Tailwind CSS
- Session isolation with secure document access

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **LLM Integration**: LangChain with OpenRouter API
- **Vector Database**: ChromaDB with HuggingFace embeddings
- **Document Processing**: Unstructured.io, LangChain loaders
- **Search**: SerpAPI for real-time web search
- **Authentication**: JWT (PyJWT) + Passlib (bcrypt)
- **Database**: SQLite with session history tracking
- **Rate Limiting**: SlowAPI
- **Session Isolation**: Python ContextVars for request-scoped session tracking

### Frontend
- **Framework**: React 19 with TypeScript
- **Routing**: React Router v7
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios with request/response interceptors
- **Markdown**: React-Markdown with GitHub Flavored Markdown (remark-gfm)
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

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration and logging
│   ├── database.py            # SQLite database operations
│   ├── security.py            # Authentication and JWT handling
│   ├── schemas.py             # Pydantic models
│   ├── routers/               # API route modules (modular design)
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── sessions.py       # Session management
│   │   ├── documents.py      # File upload and management
│   │   └── chat.py           # Chat and streaming analysis
│   └── src/                   # AI/ML components
│       ├── agent.py          # LangChain agent configuration
│       ├── tools.py          # Custom AI tools (RAG, compliance, etc.)
│       ├── core.py           # LLM and embeddings setup
│       ├── vector_store.py   # ChromaDB operations
│       ├── document_processor.py  # Document parsing
│       ├── system_prompt.py  # AI system instructions
│       └── context_vars.py   # Request-scoped session context
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Main application component
│   │   ├── api/
│   │   │   └── client.ts     # Axios client with interceptors
│   │   └── components/       # React components (modular design)
│   │       ├── Login.tsx     # Authentication UI
│   │       ├── Dashboard.tsx # Main dashboard container
│   │       ├── Sidebar.tsx   # Session list and navigation
│   │       └── ChatArea.tsx  # Chat interface and file management
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── test_suite.py              # Backend API tests
├── requirements.txt           # Python dependencies
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
- `POST /sessions/{session_id}/auto-title` - Auto-generate title (text-based heuristics)
- `DELETE /sessions/{session_id}` - Delete session
- `GET /sessions/{session_id}/history` - Get chat history

### Document Management
- `POST /upload` - Upload documents (PDF, images, Word) with `session_id` query parameter
- `GET /sessions/{session_id}/files` - List session files
- `DELETE /sessions/{session_id}/files/{file_id}` - Delete file

### Analysis
- `POST /analyze` - Analyze documents with streaming response (StreamingResponse)

## 🤖 AI Tools

The system includes specialized AI tools accessed via LangChain agent:

1. **RAG Search Tool**: Searches uploaded documents with strict session isolation using ChromaDB metadata filtering
2. **Compliance Check Tool**: Verifies regulatory compliance via SerpAPI web search
3. **Clause Comparison Tool**: Compares two legal clauses with cosine similarity scoring
4. **Citation Validation Tool**: Validates legal citations and case law using web search

## 🧪 Testing

```bash
# Run backend tests
pytest test_suite.py
```

### The test suite covers:
- User registration and authentication
- Unauthorized access protection
- Rate limiting (basic coverage)

**Note**: Full integration tests for document processing, chat streaming, and file isolation are planned but not yet implemented.

## 🔒 Security Features

- **Password Requirements**: Minimum 8 characters with bcrypt hashing
- **JWT Tokens**: Secure session management with expiration (60 minutes default)
- **Rate Limiting**: 10 requests/minute on `/upload` and `/analyze` endpoints
- **Audit Logging**: All actions logged to `audit_trail.log` with timestamps
- **Session Isolation**: Documents tagged with `source_id` and filtered per-session using ChromaDB metadata queries
- **Auto-cleanup**: Temporary files deleted after processing (unless DEBUG_MODE enabled)
- **Token Validation**: Automatic logout and redirect on invalid/expired tokens (handled by Axios interceptor)

## ⚙️ Configuration

Key configuration options in `backend/config.py`:

```python
OPENROUTER_API_KEY  # Required for LLM access
SERPAPI_API_KEY     # Optional for web search features
SECRET_KEY          # JWT signing (auto-generated if not set)
UPLOAD_DIR          # Document storage location (default: secure_uploads/)
DB_DIR              # Vector database location (default: chroma_db/)
ACCESS_TOKEN_EXPIRE_MINUTES  # Token expiration (default: 60)
SQLITE_DB           # SQLite database file (default: legal_AIagent.db)
```

## 🎨 UI Features

- **Dark/Light Theme**: Professional indigo color scheme
- **Markdown Support**: Rich text formatting with code blocks, tables, and lists
- **Message Actions**: Edit previous messages, regenerate responses
- **File Management**: Visual file cards with delete functionality
- **Session Organization**: Sidebar with inline rename and delete options
- **Responsive Design**: Mobile-friendly interface
- **Welcome Screen**: Default assistant greeting with usage instructions on new chats
- **Smart Scrolling**: Auto-scroll to latest message on updates
- **Loading States**: Visual feedback for uploads, streaming responses

## 📝 Usage Example

1. **Register/Login**: Create an account or sign in
2. **Start New Chat**: Click "New Chat" in sidebar
3. **Upload Documents**: Click upload icon to add PDFs or images
4. **Ask Questions**: Type legal questions about your documents
5. **Get AI Analysis**: Receive streaming responses with citations
6. **Manage Sessions**: Organize conversations by topic with inline renaming

## 🚀 Production Deployment

### Environment Setup
```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Set in production .env
SECRET_KEY=<generated_key>
OPENROUTER_API_KEY=<your_key>
SERPAPI_API_KEY=<your_key>  # Optional
```

### Recommended Production Stack
- **Web Server**: Nginx or Caddy (reverse proxy for both frontend and backend)
- **Process Manager**: systemd or PM2 for backend process management
- **Database**: Migrate to PostgreSQL for production (SQLite not suitable for high concurrency)
- **Storage**: S3-compatible storage for uploaded files
- **Vector DB**: Consider hosted ChromaDB or Pinecone for better scalability
- **CORS**: Update `origins` in `backend/main.py` to match production domain

### Security Hardening
```bash
# Generate strong SECRET_KEY
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Use environment variables, not .env files in production
export SECRET_KEY="..."
export OPENROUTER_API_KEY="..."

# Enable HTTPS only
# Set secure cookie flags in production
# Implement IP-based rate limiting at reverse proxy level
```

### CORS Configuration for Production
Update `backend/main.py`:
```python
origins = [
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]
```

## 🐛 Known Limitations

- **SQLite Concurrency**: SQLite is not suitable for high-concurrency production deployments. Migrate to PostgreSQL for production use.
- **Document Processing Time**: Large files may take time to process depending on file size and content complexity.
- **ChromaDB Persistence**: Vector database builds index on first document upload; ensure proper backup strategy.
- **SerpAPI Dependency**: Web search features require active SerpAPI subscription for compliance checking and citation validation.
- **Session Cleanup**: Old sessions are not automatically deleted; manual cleanup or cron job required.

## 📊 Performance Considerations

- **Vector Index Build**: First document upload per session triggers ChromaDB indexing (~2-5 seconds for typical documents)
- **Streaming Latency**: Response streaming begins within 1-2 seconds, with tokens delivered in real-time
- **Rate Limits**: 10 requests/minute on upload and analysis endpoints to prevent abuse
- **Memory Usage**: ChromaDB keeps embeddings in memory; plan for ~200MB per 1000 document chunks

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes with clear messages (`git commit -m 'Add amazing feature'`)
4. Add tests for new features
5. Ensure all tests pass (`pytest test_suite.py`)
6. Submit a pull request with detailed description

## 🐞 Troubleshooting

### Backend Issues
```bash
# Check backend logs
tail -f audit_trail.log

# Test API directly
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test1234"}'

# Verify ChromaDB
python -c "from backend.src.vector_store import get_vector_store; print(get_vector_store())"
```

### Frontend Issues
```bash
# Clear browser cache and localStorage
# Check browser console for errors
# Verify API connection
curl http://localhost:8000/docs
```

### Common Errors
- **401 Unauthorized**: Check if token is valid and not expired
- **429 Rate Limited**: Wait 60 seconds and retry
- **ChromaDB errors**: Delete `chroma_db/` folder and restart
- **Upload failures**: Check file size (<10MB recommended) and format (PDF, DOCX, PNG, JPG)

## 🙏 Acknowledgments

- Built with LangChain for AI orchestration
- ChromaDB for vector storage and semantic search
- Unstructured.io for document parsing
- OpenRouter for unified LLM access
- SerpAPI for web search capabilities
- React and Tailwind CSS for modern UI

## ⚠️ Disclaimer

This AI system is for informational purposes only and does not constitute legal advice. All outputs should be reviewed by qualified legal professionals. The system maintains audit logs and session isolation for security, but users are responsible for the confidentiality of their data.

**Data Privacy**: Uploaded documents are processed locally and sent to third-party APIs (OpenRouter, SerpAPI) for analysis. Ensure compliance with your organization's data handling policies before uploading sensitive information.

## 📄 License

This project is licensed under the MIT License.

---
**Last Updated**: December 2024  
**Maintainer**: [Oun Alawamleh/MENADevs]

For questions, issues, or feature requests, please open an issue on GitHub.
