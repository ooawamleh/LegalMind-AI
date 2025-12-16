# backend/main.py
import os
import shutil
import logging
from uuid import uuid4
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from langchain_core.messages import HumanMessage, AIMessage
from typing import List

# --- MODULE IMPORTS ---
from backend.config import UPLOAD_DIR, log_audit, SQLITE_DB
from backend.database import (
    init_db, create_user_in_db, get_user_from_db, 
    create_session_db, get_user_sessions, delete_session_db
)
from backend.security import get_password_hash, verify_password, create_access_token, get_current_user
from backend.schemas import UserModel, QueryRequest, SessionCreate, SessionResponse

# --- AI PACKAGE IMPORTS ---
from backend.src.document_processor import process_document
from backend.src.agent import agent_with_history, get_session_history

# Initialize Database
init_db()

# --- APP CONFIGURATION ---
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Legal AI Agent API",
    description="Secure, Multi-modal Legal Analysis with Real-time Search & Compliance",
    version="2.1"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: Update to allow your React Frontend URL (e.g., localhost:5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Explicit origins instead of ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTH ROUTES ---
@app.post("/register")
async def register(user: UserModel):
    hash_pw = get_password_hash(user.password)
    if create_user_in_db(user.username, hash_pw):
        log_audit(user.username, "REGISTER", "User registered successfully")
        return {"msg": "Created"}
    raise HTTPException(status_code=400, detail="User already exists")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin" and form_data.password == "admin123":
        token = create_access_token({"sub": "admin"})
        log_audit("admin", "LOGIN", "Admin backdoor access used")
        return {"access_token": token, "token_type": "bearer"}

    hashed_pw = get_user_from_db(form_data.username)
    if not hashed_pw or not verify_password(form_data.password, hashed_pw):
        log_audit(form_data.username, "LOGIN_FAILED", "Invalid credentials")
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    token = create_access_token({"sub": form_data.username})
    log_audit(form_data.username, "LOGIN", "User logged in")
    return {"access_token": token, "token_type": "bearer"}

# --- SESSION ROUTES (NEW) ---

@app.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(user: str = Depends(get_current_user)):
    """List all chat sessions for the current user."""
    sessions = get_user_sessions(user)
    return sessions

@app.post("/sessions", response_model=SessionResponse)
async def create_session(session: SessionCreate, user: str = Depends(get_current_user)):
    """Create a new chat session."""
    session_id, created_at = create_session_db(user, session.title)
    return {"session_id": session_id, "title": session.title, "created_at": created_at}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user: str = Depends(get_current_user)):
    """Delete a chat session."""
    delete_session_db(session_id, user)
    return {"status": "deleted"}

@app.get("/sessions/{session_id}/history")
async def get_history(session_id: str, user: str = Depends(get_current_user)):
    """Retrieve chat history for a specific session to populate UI."""
    # Note: Validating ownership of session_id is recommended here in production
    history_obj = get_session_history(session_id)
    messages = []
    for msg in history_obj.messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        messages.append({"role": role, "content": msg.content})
    return {"messages": messages}

# --- DOCUMENT ROUTES ---

# backend/main.py
from typing import List
# ... (Keep other imports) ...

@app.post("/upload")
@limiter.limit("10/minute")
async def upload_docs(
    request: Request, 
    files: List[UploadFile] = File(...),  # CHANGED to List
    session_id: str = "default",
    user: str = Depends(get_current_user)
):
    """
    Handle multiple file uploads (PDF, Images, Word).
    """
    results = []
    
    for file in files:
        file_id = str(uuid4())
        ext = os.path.splitext(file.filename)[1]
        safe_name = f"{file_id}{ext}"
        path = os.path.join(UPLOAD_DIR, safe_name)
        
        try:
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            chunks = process_document(path)
            results.append({"filename": file.filename, "chunks": chunks, "status": "Success"})
            log_audit(user, "UPLOAD", f"Processed {file.filename} for session {session_id}")
            
        except Exception as e:
            results.append({"filename": file.filename, "status": "Error", "detail": str(e)})
            log_audit(user, "UPLOAD_ERROR", f"Failed {file.filename}: {str(e)}")
            if os.path.exists(path):
                os.remove(path)
            raise HTTPException(status_code=500, detail=str(e))
    return {"uploaded": results}
        

# --- ANALYSIS ROUTES ---

def stream_generator(query: str, session_id: str):
    """
    Generator using session_id for history context.
    """
    try:
        # Use session_id specifically for this chat
        for chunk in agent_with_history.stream(
            {"input": query},
            config={"configurable": {"session_id": session_id}}
        ):
            if isinstance(chunk, dict) and "output" in chunk:
                yield str(chunk["output"])
            elif isinstance(chunk, dict) and "actions" in chunk:
                yield "\n\n*Checking legal sources...*\n\n"
                
    except Exception as e:
        logging.error(f"Stream Error for session {session_id}: {e}")
        yield f"\n[System Error]: {str(e)}"

@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze(
    request: Request, 
    q: QueryRequest, 
    user: str = Depends(get_current_user)
):
    """
    Main analysis endpoint. Streams the answer back to the client.
    """
    # Use q.session_id passed from frontend
    log_audit(user, "ANALYZE", f"Session: {q.session_id} | Query: {q.query}")
    return StreamingResponse(
        stream_generator(q.query, q.session_id), 
        media_type="text/plain"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# # backend/main.py
# import os
# import shutil
# import logging
# from uuid import uuid4
# from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
# from fastapi.responses import StreamingResponse
# from fastapi.security import OAuth2PasswordRequestForm
# from fastapi.middleware.cors import CORSMiddleware
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded

# # --- MODULE IMPORTS ---
# from backend.config import UPLOAD_DIR, log_audit
# from backend.database import init_db, create_user_in_db, get_user_from_db
# from backend.security import get_password_hash, verify_password, create_access_token, get_current_user
# from backend.schemas import UserModel, QueryRequest

# # --- AI PACKAGE IMPORTS ---
# # Logic is now imported from the modular 'backend.ai' package
# from backend.src.document_processor import process_document
# from backend.src.agent import agent_with_history

# # Initialize Database
# init_db()

# # --- APP CONFIGURATION ---
# limiter = Limiter(key_func=get_remote_address)
# app = FastAPI(
#     title="Legal AI Agent API",
#     description="Secure, Multi-modal Legal Analysis with Real-time Search & Compliance",
#     version="2.1"
# )
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# # CORS: Allow all for dev/demo; restrict in actual production
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- AUTH ROUTES ---

# @app.post("/register")
# async def register(user: UserModel):
#     """Register a new user with hashed password."""
#     hash_pw = get_password_hash(user.password)
#     if create_user_in_db(user.username, hash_pw):
#         log_audit(user.username, "REGISTER", "User registered successfully")
#         return {"msg": "Created"}
#     raise HTTPException(status_code=400, detail="User already exists")

# @app.post("/token")
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     """OAuth2 compatible token login."""
    
#     # 1. Check for Admin Backdoor explicitly
#     if form_data.username == "admin" and form_data.password == "admin123":
#         token = create_access_token({"sub": "admin"})
#         log_audit("admin", "LOGIN", "Admin backdoor access used")
#         return {"access_token": token, "token_type": "bearer"}

#     # 2. Regular User Login
#     hashed_pw = get_user_from_db(form_data.username)
    
#     # Verify using standard DB check
#     if not hashed_pw or not verify_password(form_data.password, hashed_pw):
#         # Log failed attempt
#         log_audit(form_data.username, "LOGIN_FAILED", "Invalid credentials")
#         raise HTTPException(status_code=400, detail="Invalid username or password")
    
#     token = create_access_token({"sub": form_data.username})
#     log_audit(form_data.username, "LOGIN", "User logged in")
#     return {"access_token": token, "token_type": "bearer"}

# # --- DOCUMENT ROUTES ---

# @app.post("/upload")
# @limiter.limit("5/minute")
# async def upload_doc(
#     request: Request, 
#     file: UploadFile = File(...), 
#     user: str = Depends(get_current_user)
# ):
#     """
#     Secure file upload.
#     1. Saves file temporarily with a UUID.
#     2. Processes it via the AI engine (OCR/Text Split).
#     3. Deletes the file immediately after processing.
#     """
#     file_id = str(uuid4())
#     ext = os.path.splitext(file.filename)[1]
#     safe_name = f"{file_id}{ext}"
#     path = os.path.join(UPLOAD_DIR, safe_name)
    
#     try:
#         with open(path, "wb") as f:
#             shutil.copyfileobj(file.file, f)
        
#         # Process document using the imported module
#         chunks_count = process_document(path)
        
#         log_audit(user, "UPLOAD", f"File {file.filename} processed. Chunks: {chunks_count}")
#         return {
#             "filename": file.filename, 
#             "chunks": chunks_count, 
#             "status": "Processed & Deleted securely"
#         }
#     except Exception as e:
#         log_audit(user, "UPLOAD_ERROR", str(e))
#         # Ensure cleanup happens even on error (redundancy is good)
#         if os.path.exists(path):
#             os.remove(path)
#         raise HTTPException(status_code=500, detail=str(e))

# # --- ANALYSIS ROUTES ---

# def stream_generator(query: str, user_id: str):
#     """
#     Generator for streaming LLM responses.
#     Iterates over the LangChain runnable stream.
#     """
#     try:
#         # Configurable session_id allows different users to have separate chat histories
#         for chunk in agent_with_history.stream(
#             {"input": query},
#             config={"configurable": {"session_id": user_id}}
#         ):
#             # Check for final text output
#             if isinstance(chunk, dict) and "output" in chunk:
#                 yield str(chunk["output"])
            
#             # Check for intermediate tool actions (optional: inform user UI)
#             elif isinstance(chunk, dict) and "actions" in chunk:
#                 # You can customize this message or remove it for a seamless feel
#                 yield "\n\n*Checking legal sources...*\n\n"
                
#     except Exception as e:
#         logging.error(f"Stream Error for user {user_id}: {e}")
#         yield f"\n[System Error]: An error occurred while processing your request: {str(e)}"

# @app.post("/analyze")
# @limiter.limit("10/minute")
# async def analyze(
#     request: Request, 
#     q: QueryRequest, 
#     user: str = Depends(get_current_user)
# ):
#     """
#     Main analysis endpoint. Streams the answer back to the client.
#     """
#     log_audit(user, "ANALYZE", q.query)
#     return StreamingResponse(
#         stream_generator(q.query, user), 
#         media_type="text/plain"
#     )

# if __name__ == "__main__":
#     import uvicorn
#     # In production, you would run this via: gunicorn -k uvicorn.workers.UvicornWorker ...
#     uvicorn.run(app, host="0.0.0.0", port=8000)
