# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.database import init_db
from backend.routers import auth, sessions, documents, chat

init_db()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Legal AI Agent API", version="3.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(documents.router)
app.include_router(chat.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# # backend/main.py
# import os
# import shutil
# import logging
# from uuid import uuid4
# from typing import List
# from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
# from fastapi.responses import StreamingResponse
# from fastapi.security import OAuth2PasswordRequestForm
# from fastapi.middleware.cors import CORSMiddleware
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded
# from langchain_core.messages import HumanMessage
# from pydantic import BaseModel

# # --- MODULE IMPORTS ---
# from backend.config import UPLOAD_DIR, log_audit
# from backend.database import (
#     init_db, create_user_in_db, get_user_from_db, 
#     create_session_db, get_user_sessions, delete_session_db,
#     update_session_title_db, add_file_to_session_db, get_session_files_db, delete_file_db
# )
# from backend.security import get_password_hash, verify_password, create_access_token, get_current_user
# from backend.schemas import UserModel, QueryRequest, SessionCreate, SessionResponse

# # --- AI PACKAGE IMPORTS ---
# from backend.src.core import llm  # Imported for Auto-Titling
# from backend.src.document_processor import process_document
# from backend.src.agent import agent_with_history, get_session_history
# from backend.src.vector_store import delete_from_vector_store

# # Initialize Database
# init_db()

# # --- APP CONFIGURATION ---
# limiter = Limiter(key_func=get_remote_address)
# app = FastAPI(
#     title="Legal AI Agent API",
#     description="Secure, Multi-modal Legal Analysis with Real-time Search & Compliance",
#     version="2.3"
# )
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# # CORS: Allow Frontend Access
# origins = [
#     "http://localhost:5173",
#     "http://127.0.0.1:5173",
#     "http://localhost:3000",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- NEW SCHEMAS ---
# class RenameRequest(BaseModel):
#     title: str

# class TitleGenRequest(BaseModel):
#     query: str

# class FileResponse(BaseModel):
#     file_id: str
#     filename: str

# # --- AUTH ROUTES ---

# @app.post("/register")
# async def register(user: UserModel):
#     hash_pw = get_password_hash(user.password)
#     if create_user_in_db(user.username, hash_pw):
#         log_audit(user.username, "REGISTER", "User registered successfully")
#         return {"msg": "Created"}
#     raise HTTPException(status_code=400, detail="User already exists")

# @app.post("/token")
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     # Admin Backdoor
#     if form_data.username == "admin" and form_data.password == "admin123":
#         token = create_access_token({"sub": "admin"})
#         log_audit("admin", "LOGIN", "Admin backdoor access used")
#         return {"access_token": token, "token_type": "bearer"}

#     hashed_pw = get_user_from_db(form_data.username)
#     if not hashed_pw or not verify_password(form_data.password, hashed_pw):
#         log_audit(form_data.username, "LOGIN_FAILED", "Invalid credentials")
#         raise HTTPException(status_code=400, detail="Invalid username or password")
    
#     token = create_access_token({"sub": form_data.username})
#     log_audit(form_data.username, "LOGIN", "User logged in")
#     return {"access_token": token, "token_type": "bearer"}

# # --- SESSION ROUTES ---

# @app.get("/sessions", response_model=List[SessionResponse])
# async def list_sessions(user: str = Depends(get_current_user)):
#     """List all chat sessions for the current user."""
#     return get_user_sessions(user)

# @app.post("/sessions", response_model=SessionResponse)
# async def create_session(session: SessionCreate, user: str = Depends(get_current_user)):
#     """Create a new chat session."""
#     session_id, created_at = create_session_db(user, session.title)
#     return {"session_id": session_id, "title": session.title, "created_at": created_at}

# @app.patch("/sessions/{session_id}")
# async def rename_session(session_id: str, req: RenameRequest, user: str = Depends(get_current_user)):
#     """Manually rename a session."""
#     update_session_title_db(session_id, req.title)
#     return {"status": "updated", "title": req.title}

# @app.post("/sessions/{session_id}/auto-title")
# # backend/main.py

# @app.post("/sessions/{session_id}/auto-title")
# async def auto_generate_title(
#     session_id: str, 
#     req: TitleGenRequest, 
#     user: str = Depends(get_current_user)
# ):
#     """
#     Generates a title WITHOUT using an LLM.
#     Uses simple text processing rules for speed and zero cost.
#     """
#     query = req.query.strip()
#     lower_query = query.lower()
    
#     # 1. Detect Greetings
#     greetings = ["hello", "hi", "hey", "good morning", "good evening", "greetings"]
#     # Check if the query IS a greeting or STARTS with a greeting followed by nothing important
#     if lower_query in greetings or (len(query.split()) < 2 and lower_query.replace('!', '') in greetings):
#         new_title = "General Discussion"
        
#     else:
#         # 2. Smart Truncation
#         # Split into words
#         words = query.split()
        
#         # If it's short (<= 5 words), use the whole thing
#         if len(words) <= 5:
#             new_title = query
#         else:
#             # Take the first 5 words and add "..."
#             new_title = " ".join(words[:5]) + "..."
            
#         # Capitalize first letter just in case
#         new_title = new_title[:50] # Hard cap at 50 chars for safety
#         new_title = new_title.capitalize()

#     # Update DB
#     update_session_title_db(session_id, new_title)
#     return {"title": new_title}

# @app.delete("/sessions/{session_id}")
# async def delete_session(session_id: str, user: str = Depends(get_current_user)):
#     """Delete a chat session and all associated files."""
#     delete_session_db(session_id, user)
#     return {"status": "deleted"}

# @app.get("/sessions/{session_id}/history")
# async def get_history(session_id: str, user: str = Depends(get_current_user)):
#     """Retrieve chat history."""
#     history_obj = get_session_history(session_id)
#     messages = []
#     for msg in history_obj.messages:
#         role = "user" if isinstance(msg, HumanMessage) else "assistant"
#         messages.append({"role": role, "content": msg.content})
#     return {"messages": messages}

# # --- FILE MANAGEMENT ROUTES ---

# @app.get("/sessions/{session_id}/files", response_model=List[FileResponse])
# async def list_files(session_id: str, user: str = Depends(get_current_user)):
#     """List uploaded files for a session."""
#     return get_session_files_db(session_id)

# @app.delete("/sessions/{session_id}/files/{file_id}")
# async def delete_file(session_id: str, file_id: str, user: str = Depends(get_current_user)):
#     """Delete a file from SQL and Vector Database."""
#     # 1. Remove from Vector DB
#     delete_from_vector_store(file_id)
#     # 2. Remove from SQL DB
#     delete_file_db(file_id)
#     return {"status": "deleted"}

# # --- UPLOAD ROUTE ---

# @app.post("/upload")
# @limiter.limit("10/minute")
# async def upload_docs(
#     request: Request, 
#     files: List[UploadFile] = File(...), 
#     session_id: str = "default",
#     user: str = Depends(get_current_user)
# ):
#     """
#     Handle multiple file uploads. Tags content with file_uuid for future deletion.
#     """
#     results = []
    
#     for file in files:
#         file_uuid = str(uuid4()) # Unique ID for this specific file
#         ext = os.path.splitext(file.filename)[1]
#         safe_name = f"{file_uuid}{ext}"
#         path = os.path.join(UPLOAD_DIR, safe_name)
        
#         try:
#             with open(path, "wb") as f:
#                 shutil.copyfileobj(file.file, f)
            
#             # Process and tag with file_uuid
#             # Ensure process_document handles the second argument (file_id)
#             chunks = process_document(path, file_uuid)
            
#             # Save mapping to DB
#             if chunks > 0:
#                 add_file_to_session_db(session_id, file.filename, file_uuid)

#             results.append({
#                 "filename": file.filename, 
#                 "file_id": file_uuid,
#                 "chunks": chunks, 
#                 "status": "Success"
#             })
#             log_audit(user, "UPLOAD", f"Processed {file.filename} for session {session_id}")
            
#         except Exception as e:
#             results.append({"filename": file.filename, "status": "Error", "detail": str(e)})
#             log_audit(user, "UPLOAD_ERROR", f"Failed {file.filename}: {str(e)}")
#             if os.path.exists(path):
#                 os.remove(path)

#     return {"uploaded": results}

# # --- ANALYSIS ROUTE ---

# def stream_generator(query: str, session_id: str):
#     """
#     Generator using session_id for history context.
#     """
#     try:
#         # Use session_id specifically for this chat
#         for chunk in agent_with_history.stream(
#             {"input": query},
#             config={"configurable": {"session_id": session_id}}
#         ):
#             if isinstance(chunk, dict) and "output" in chunk:
#                 yield str(chunk["output"])
#             elif isinstance(chunk, dict) and "actions" in chunk:
#                 yield "\n\n*Checking legal sources...*\n\n"
                
#     except Exception as e:
#         logging.error(f"Stream Error for session {session_id}: {e}")
#         yield f"\n[System Error]: {str(e)}"

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
#     log_audit(user, "ANALYZE", f"Session: {q.session_id} | Query: {q.query}")
#     return StreamingResponse(
#         stream_generator(q.query, q.session_id), 
#         media_type="text/plain"
#     )

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
