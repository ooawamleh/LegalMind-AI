# backend/routers/chat.py
import logging
import asyncio
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from contextvars import copy_context

from backend.security import get_current_user
from backend.schemas import QueryRequest
from backend.config import log_audit
from backend.src.agent import agent_with_history
from backend.src.context_vars import session_context

router = APIRouter(tags=["chat"])

async def async_stream_generator(query: str, session_id: str):
    """
    Async Generator.
    This runs directly in the async event loop, avoiding the threadpool context switch issue.
    """
    # 1. Set Context
    token = session_context.set(session_id)
    
    try:
        # 2. Iterate over the async stream from LangChain
        async for chunk in agent_with_history.astream(
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
        
    finally:
        # 3. Cleanup
        session_context.reset(token)

@router.post("/analyze")
async def analyze(request: Request, q: QueryRequest, user: str = Depends(get_current_user)):
    log_audit(user, "ANALYZE", f"Session: {q.session_id} | Query: {q.query}")
    
    # CHANGE: Use the async generator directly
    return StreamingResponse(
        async_stream_generator(q.query, q.session_id), 
        media_type="text/plain"
    )

# # backend/routers/chat.py
# import logging
# from fastapi import APIRouter, Depends, Request
# from fastapi.responses import StreamingResponse

# from backend.security import get_current_user
# from backend.schemas import QueryRequest
# from backend.config import log_audit
# from backend.src.agent import agent_with_history
# from backend.src.context_vars import session_context 

# router = APIRouter(tags=["chat"])

# def stream_generator(query: str, session_id: str):
#     """
#     Generator using session_id for history context.
#     Sets the session_context so tools can filter documents.
#     """
#     # 1. Set the Session ID in the global context
#     token = session_context.set(session_id)
    
#     try:
#         # 2. Run the Agent (Tools will now be able to read session_context)
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
        
#     finally:
#         # 3. Clean up the context
#         session_context.reset(token)

# @router.post("/analyze")
# async def analyze(request: Request, q: QueryRequest, user: str = Depends(get_current_user)):
#     log_audit(user, "ANALYZE", f"Session: {q.session_id} | Query: {q.query}")
#     return StreamingResponse(
#         stream_generator(q.query, q.session_id), 
#         media_type="text/plain"
#     )