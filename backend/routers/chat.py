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
    history = await run_in_threadpool(get_session_history, session_id)
    chat_history = await run_in_threadpool(lambda: history.messages)
    
    full_response = ""
    
    # --- BUFFERING STATE ---
    # We hold text here until we know if it's a preamble ("To determine...") or a real answer
    pre_tool_buffer = "" 
    tool_has_started = False
    
    try:
        # 2. Stream from the Agent Executor Directly (Async)
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
                content = chunk.content
                
                # FILTER: Block Internal Retrieval thoughts based on the tag
                if "internal_retrieval" in tags:
                    continue

                # FILTER: Ignore tool arguments
                if hasattr(chunk, "tool_call_chunks") and len(chunk.tool_call_chunks) > 0:
                    continue

                # FILTER: Ignore internal RAG thoughts (legacy check)
                metadata = event.get("metadata", {})
                if metadata.get("langchain_author") != "rag_search_tool":
                    if content:
                        if not tool_has_started:
                            # --- DANGER ZONE (Before Tool) ---
                            # Buffer text like "To determine..." or "I will search..."
                            # We do NOT yield this yet.
                            pre_tool_buffer += content
                            
                            # Safety Valve: If the buffer gets long (> 200 chars), 
                            # it's likely a direct answer (e.g., "Hello!"), so we flush it.
                            if len(pre_tool_buffer) > 200: 
                                 yield pre_tool_buffer
                                 full_response += pre_tool_buffer
                                 pre_tool_buffer = ""
                                 tool_has_started = True
                        else:
                            # --- SAFE ZONE (After Tool) ---
                            # The tool has run, so this is the real answer. Yield immediately.
                            yield content
                            full_response += content

            elif kind == "on_tool_start":
                # Check for any of our known tools
                if event["name"] in ["rag_search_tool", "compliance_check_tool", "clause_comparison_tool", "citation_validation_tool"]:
                    # --- THE FIX ---
                    # A tool just started. The buffer contained the "To determine..." preamble.
                    # We DELETE the buffer so the user never sees it.
                    pre_tool_buffer = "" 
                    tool_has_started = True
                    yield f"\n\n*Analyzing...*\n\n"

        # 3. End of Stream Check
        # If no tool was ever called (e.g., just "Hello"), flush the buffer now.
        if pre_tool_buffer:
            yield pre_tool_buffer
            full_response += pre_tool_buffer

        # 4. Save History Manually (Sync DB Access)
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
