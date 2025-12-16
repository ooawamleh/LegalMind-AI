# backend/ai/tools.py
from langchain_core.tools import tool
from langchain_community.utilities import SerpAPIWrapper
from langchain.retrievers.multi_query import MultiQueryRetriever
from backend.config import SERPAPI_API_KEY
from backend.src.core import llm
from backend.src.vector_store import get_vector_store, get_cosine_similarity


# --- TOOLS ---

@tool
def rag_search_tool(query: str) -> str:
    """
    Search the uploaded legal document or contract for specific information.
    Useful for finding definitions, clauses, dates, or parties in the text.
    """
    db = get_vector_store()

    # Use MultiQueryRetriever to expand queries dynamically
    base_retriever = db.as_retriever(search_type="mmr", search_kwargs={"k": 8, "fetch_k": 25})
    retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm
    )

    docs = retriever.get_relevant_documents(query)

    # Deduplicate results
    seen = set()
    unique_docs = []
    for d in docs:
        if d.page_content not in seen:
            seen.add(d.page_content)
            unique_docs.append(d)

    if not unique_docs:
        print("❌ [RAG Tool] No results found.")  # DEBUG
        return "System Notification: No relevant information found in the uploaded documents. Do not invent an answer."

    # LOG the snippets found (First 200 chars)
    for doc in unique_docs[:3]:
        print(f"✅ [RAG Tool] Retrieved chunk preview:\n{doc.page_content[:200]}...\n")  # DEBUG

    # FORMAT output with strict grounding instruction
    results = []
    for i, d in enumerate(unique_docs):
        results.append(f"Chunk {i+1}:\n{d.page_content}")

    context_str = "\n\n".join(results)
    return (
        f"DOCUMENT CONTEXT:\n{context_str}\n\n"
        "STRICT INSTRUCTION:\n"
        "- Only answer using the exact text above.\n"
        "- Quote clauses verbatim.\n"
        "- If the answer is not present, respond with: 'I cannot find that information in the document.'\n"
        "- Do not paraphrase or add external context unless explicitly asked."
    )


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
        except Exception as e:
            validation_data = f"Search failed: {e}"
    else:
        return "Search API key missing. Cannot validate citation."

    # Strict instruction: do not infer content if exact text is missing
    prompt = f"""
Validate this legal citation using the search data below.
Data: {validation_data}
Citation: {query}

STRICT INSTRUCTION:
- Confirm whether the citation exists and is valid.
- If the exact text of the citation is not found, say: "I cannot find the exact wording, but the citation exists and is valid."
- Do not infer or paraphrase the content of the citation.
"""
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
