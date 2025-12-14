# backend/ai/tools.py
from langchain_core.tools import tool
from langchain_community.utilities import SerpAPIWrapper
from backend.config import SERPAPI_API_KEY
from backend.engine.core import llm
from backend.engine.vector_store import get_vector_store, get_cosine_similarity

# --- TOOLS ---

@tool
def rag_search_tool(query: str) -> str:
    """
    Search the uploaded legal document or contract for specific information.
    Useful for finding definitions, clauses, dates, or parties in the text.
    """
    db = get_vector_store()
    # Fetch more docs (k=4) to ensure coverage
    retriever = db.as_retriever(search_type="mmr", search_kwargs={"k": 4, "fetch_k": 20})
    docs = retriever.invoke(query)
    
    # Deduplicate results
    seen = set()
    unique_docs = []
    for d in docs:
        if d.page_content not in seen:
            seen.add(d.page_content)
            unique_docs.append(d)
            
    if not unique_docs:
        return "No relevant information found in the document."
        
    return "\n\n".join([d.page_content for d in unique_docs])

@tool
def compliance_check_tool(query: str) -> str:
    """
    Checks real-time regulatory compliance using web search.
    Use this to find current laws (GDPR, CCPA, etc.) or recent legal changes.
    """
    search_results = ""
    if SERPAPI_API_KEY:
        try:
            search = SerpAPIWrapper(serpapi_api_key=SERPAPI_API_KEY)
            search_results = search.run(f"current legal regulations {query}")
        except Exception as e:
            search_results = f"Search failed: {e}"
    else:
        return "Search API key is missing. Cannot check external compliance."
    
    prompt = f"Check regulatory compliance based on these search results:\n{search_results}\n\nQuery: {query}"
    response = llm.invoke(prompt)
    return getattr(response, "content", str(response))

@tool
def clause_comparison_tool(query: str) -> str:
    """
    Compares two legal clauses for similarity and differences.
    Input must be two clauses separated by a pipe '|' symbol. 
    Example: "Clause A text | Clause B text"
    """
    if "|" not in query:
        return "Error: Input must contain '|' to separate the two clauses."
    
    c1, c2 = query.split("|", 1)
    similarity = get_cosine_similarity(c1.strip(), c2.strip())
    
    prompt = f"""Compare these two clauses.
    Cosine Similarity Score: {similarity:.4f}
    
    Clause 1: {c1}
    Clause 2: {c2}
    
    Provide a legal analysis of differences."""
    
    response = llm.invoke(prompt)
    return getattr(response, "content", str(response))

@tool
def citation_validation_tool(query: str) -> str:
    """
    Validates if a specific legal citation, case law, or statute is real and accurate.
    Uses web search to verify existence.
    """
    validation_data = ""
    if SERPAPI_API_KEY:
        try:
            search = SerpAPIWrapper(serpapi_api_key=SERPAPI_API_KEY)
            validation_data = search.run(f"legal citation {query}")
        except:
            validation_data = "Search unavailable."
    else:
        return "Search API key missing. Cannot validate citation."

    prompt = f"Validate this legal citation using the search data:\nData: {validation_data}\nCitation: {query}"
    response = llm.invoke(prompt)
    return getattr(response, "content", str(response))

# Export list of tools
# note: calling the decorated function without () passes the tool object
tools = [
    rag_search_tool,
    compliance_check_tool,
    clause_comparison_tool,
    citation_validation_tool,
]
