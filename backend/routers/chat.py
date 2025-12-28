# backend/routers/chat.py
import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool # To run sync DB calls safely

from backend.security import get_current_user
from backend.schemas import QueryRequest
from backend.config import log_audit
from backend.src.agent import agent_executor, get_session_history # Import executor directly
from backend.src.context_vars import session_context 

router = APIRouter(tags=["chat"])

async def async_stream_generator(query: str, session_id: str):
    token = session_context.set(session_id)
    
    # 1. Load History Synchronously (Safe DB Access)
    # We use run_in_threadpool to keep the event loop non-blocking
    history = await run_in_threadpool(get_session_history, session_id)
    chat_history = await run_in_threadpool(lambda: history.messages)
    
    full_response = ""
    
    try:
        # 2. Stream from the Agent Executor Directly (Async)
        # We pass 'chat_history' manually, bypassing the wrapper conflicts
        async for event in agent_executor.astream_events(
            {
                "input": query, 
                "chat_history": chat_history
            },
            config={"configurable": {"session_id": session_id}},
            version="v2"
        ):
            kind = event["event"]
            tags = event.get("tags", [])

            # --- Logic to Filter Output ---
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                
                # CHANGE: Block Internal Retrieval thoughts based on the tag
                if "internal_retrieval" in tags:
                    continue

                # Ignore tool arguments
                if hasattr(chunk, "tool_call_chunks") and len(chunk.tool_call_chunks) > 0:
                    continue

                # Ignore internal RAG thoughts (legacy check, keeping for safety)
                metadata = event.get("metadata", {})
                if metadata.get("langchain_author") != "rag_search_tool":
                    content = chunk.content
                    if content:
                        full_response += content # Accumulate for saving later
                        yield content

            elif kind == "on_tool_start":
                if event["name"] in ["rag_search_tool", "compliance_check_tool"]:
                    yield f"\n\n*Analyzing document...*\n\n"

        # 3. Save History Manually (Sync DB Access)
        # Now that streaming is done, we save the user query and the AI response
        if full_response.strip():
            await run_in_threadpool(history.add_user_message, query)
            await run_in_threadpool(history.add_ai_message, full_response)

    except Exception as e:
        logging.error(f"Stream Error for session {session_id}: {e}")
        yield f"\n[System Error]: {str(e)}"
        
    finally:
        session_context.reset(token)

@router.post("/analyze")
async def analyze(request: Request, q: QueryRequest, user: str = Depends(get_current_user)):
    log_audit(user, "ANALYZE", f"Session: {q.session_id} | Query: {q.query}")
    return StreamingResponse(
        async_stream_generator(q.query, q.session_id), 
        media_type="text/plain"
    )
