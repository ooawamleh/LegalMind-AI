# backend/schemas.py
from pydantic import BaseModel
from typing import List, Optional

# --- USER AUTH ---
class UserModel(BaseModel):
    username: str
    password: str

# --- CHAT & SEARCH ---
class QueryRequest(BaseModel):
    query: str
    session_id: str

# --- SESSION MANAGEMENT ---
class SessionCreate(BaseModel):
    title: str

class SessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: str

class RenameRequest(BaseModel):
    title: str

class TitleGenRequest(BaseModel):
    query: str

# --- FILE MANAGEMENT ---
class FileResponse(BaseModel):
    file_id: str
    filename: str