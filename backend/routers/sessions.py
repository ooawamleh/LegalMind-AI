# backend/routers/sessions.py
from typing import List
from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage

from backend.database import (
    create_session_db, get_user_sessions, delete_session_db,
    update_session_title_db, get_session_files_db
)
from backend.security import get_current_user
from backend.schemas import SessionCreate, SessionResponse, RenameRequest, TitleGenRequest
from backend.src.agent import get_session_history

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.get("", response_model=List[SessionResponse])
async def list_sessions(user: str = Depends(get_current_user)):
    return get_user_sessions(user)

@router.post("", response_model=SessionResponse)
async def create_session(session: SessionCreate, user: str = Depends(get_current_user)):
    session_id, created_at = create_session_db(user, session.title)
    return {"session_id": session_id, "title": session.title, "created_at": created_at}

@router.patch("/{session_id}")
async def rename_session(session_id: str, req: RenameRequest, user: str = Depends(get_current_user)):
    update_session_title_db(session_id, req.title)
    return {"status": "updated", "title": req.title}

@router.post("/{session_id}/auto-title")
async def auto_generate_title(session_id: str, req: TitleGenRequest, user: str = Depends(get_current_user)):
    # 1. PRIORITY: Check if the session has files
    session_files = get_session_files_db(session_id)
    
    if session_files:
        # If files exist, use the first filename as the title
        filename = session_files[0]['filename']
        
        # Optional: Remove the file extension (e.g., .pdf) for a cleaner look
        if "." in filename:
            filename = filename.rsplit(".", 1)[0]
            
        new_title = f"📄 {filename}"
        
    else:
        # 2. FALLBACK: Use the User's Query
        query = req.query.strip()
        lower_query = query.lower()
        
        greetings = ["hello", "hi", "hey", "good morning", "greetings"]
        
        # Ignore short greetings
        if lower_query in greetings or (len(query.split()) < 2 and lower_query.replace('!', '') in greetings):
            new_title = "General Discussion"
        else:
            # Generate title from the first few words
            words = query.split()
            if len(words) <= 5:
                new_title = query
            else:
                new_title = " ".join(words[:5]) + "..."
            new_title = new_title[:50].capitalize()

    # Save and return
    update_session_title_db(session_id, new_title)
    return {"title": new_title}

@router.delete("/{session_id}")
async def delete_session(session_id: str, user: str = Depends(get_current_user)):
    delete_session_db(session_id, user)
    return {"status": "deleted"}

@router.get("/{session_id}/history")
async def get_history(session_id: str, user: str = Depends(get_current_user)):
    history_obj = get_session_history(session_id)
    messages = []
    for msg in history_obj.messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        messages.append({"role": role, "content": msg.content})
    return {"messages": messages}