# # backend/src/vector_store.py
# import numpy as np
# from langchain_community.vectorstores import Chroma
# from backend.config import DB_DIR
# from backend.src.core import embeddings

# def get_vector_store():
#     """Returns the ChromaDB instance."""
#     return Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

# def get_cosine_similarity(text1, text2):
#     """Calculates cosine similarity between two text strings."""
#     vec1 = embeddings.embed_query(text1)
#     vec2 = embeddings.embed_query(text2)
#     dot_product = np.dot(vec1, vec2)
#     norm1 = np.linalg.norm(vec1)
#     norm2 = np.linalg.norm(vec2)
#     return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0

# backend/src/vector_store.py
import numpy as np
from langchain_community.vectorstores import Chroma
from backend.config import DB_DIR
from backend.src.core import embeddings

def get_vector_store():
    return Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

def delete_from_vector_store(file_id: str):
    """Removes all chunks associated with a specific file_id."""
    db = get_vector_store()
    # Chroma allows deletion by metadata filter
    try:
        # We need to ensure we query by the metadata 'source_id' we will inject
        db._collection.delete(where={"source_id": file_id}) 
        return True
    except Exception as e:
        print(f"Vector delete error: {e}")
        return False

def get_cosine_similarity(text1, text2):
    vec1 = embeddings.embed_query(text1)
    vec2 = embeddings.embed_query(text2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0