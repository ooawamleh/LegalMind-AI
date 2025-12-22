# backend/routers/documents.py
import os
import shutil
from uuid import uuid4
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, Request

from backend.config import UPLOAD_DIR, log_audit
from backend.database import add_file_to_session_db, get_session_files_db, delete_file_db
from backend.security import get_current_user
from backend.schemas import FileResponse
from backend.src.document_processor import process_document
from backend.src.vector_store import delete_from_vector_store

router = APIRouter(tags=["documents"])

@router.get("/sessions/{session_id}/files", response_model=List[FileResponse])
async def list_files(session_id: str, user: str = Depends(get_current_user)):
    return get_session_files_db(session_id)

@router.delete("/sessions/{session_id}/files/{file_id}")
async def delete_file(session_id: str, file_id: str, user: str = Depends(get_current_user)):
    delete_from_vector_store(file_id)
    delete_file_db(file_id)
    return {"status": "deleted"}

@router.post("/upload")
async def upload_docs(
    request: Request, 
    files: List[UploadFile] = File(...), 
    session_id: str = "default",
    user: str = Depends(get_current_user)
):
    results = []
    for file in files:
        file_uuid = str(uuid4())
        ext = os.path.splitext(file.filename)[1]
        safe_name = f"{file_uuid}{ext}"
        path = os.path.join(UPLOAD_DIR, safe_name)
        
        try:
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            chunks = process_document(path, file_uuid)
            
            if chunks > 0:
                add_file_to_session_db(session_id, file.filename, file_uuid)

            results.append({
                "filename": file.filename, "file_id": file_uuid,
                "chunks": chunks, "status": "Success"
            })
            log_audit(user, "UPLOAD", f"Processed {file.filename}")
            
        except Exception as e:
            results.append({"filename": file.filename, "status": "Error", "detail": str(e)})
            log_audit(user, "UPLOAD_ERROR", f"Failed {file.filename}: {str(e)}")
            if os.path.exists(path): os.remove(path)

    return {"uploaded": results}