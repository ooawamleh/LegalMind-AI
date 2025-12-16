# backend/src/document_processor.py
import os
import base64
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_unstructured import UnstructuredLoader
from langchain_core.messages import HumanMessage
from langchain_community.vectorstores.utils import filter_complex_metadata

from backend.src.core import llm
from backend.src.vector_store import get_vector_store

def refine_chunks(docs):
    """Further split clauses (a), (b), (c), (d) into smaller retrievable chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n(a)", "\n(b)", "\n(c)", "\n(d)", "\n\n"]
    )
    refined = []
    for doc in docs:
        refined.extend(
            splitter.create_documents([doc.page_content], metadatas=[doc.metadata])
        )
    return refined

def process_document(file_path: str):
    try:
        splits = []
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # --- CASE 1: IMAGES (LLM Vision) ---
        if file_ext in ['.png', '.jpg', '.jpeg']:
            logging.info("🖼️ Processing Image with LLM Vision...")
            with open(file_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": "Transcribe this legal document. Capture all headers and clauses accurately."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            )
            response = llm.invoke([message])
            if isinstance(response.content, str) and response.content.strip():
                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                splits = splitter.create_documents([response.content.strip()])
            else:
                return 0

        # --- CASE 2: PDFs & WORD DOCS ---
        elif file_ext in ['.pdf', '.docx', '.doc']:
            logging.info(f"📄 Processing {file_ext} with Structural Chunking...")
            # UnstructuredLoader handles .docx natively
            loader = UnstructuredLoader(
                file_path,
                chunking_strategy="by_title",
                max_characters=2000,
                new_after_n_chars=1500,
                combine_text_under_n_chars=500,
            )
            splits = loader.load()
            
            if splits:
                splits = refine_chunks(splits)

        # --- COMMON: CLEAN & STORE ---
        if splits:
            cleaned_splits = filter_complex_metadata(splits)
            valid_splits = [doc for doc in cleaned_splits if doc.page_content.strip()]
            
            if valid_splits:
                vectorstore = get_vector_store()
                vectorstore.add_documents(valid_splits)
                logging.info(f"✅ Added {len(valid_splits)} chunks to DB.")
                return len(valid_splits)
        
        return 0

    except Exception as e:
        logging.error(f"❌ Error processing document: {str(e)}")
        raise e
    finally:
        if os.getenv("DEBUG_MODE", "false").lower() != "true":
            if os.path.exists(file_path):
                os.remove(file_path)

# # backend/ai/document_processor.py
# import os
# import base64
# import logging
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_unstructured import UnstructuredLoader
# from langchain_core.messages import HumanMessage
# # NEW IMPORT: Utility to fix the metadata crash
# from langchain_community.vectorstores.utils import filter_complex_metadata

# from backend.src.core import llm
# from backend.src.vector_store import get_vector_store

# def process_document(file_path: str):
#     """
#     Processes a PDF or Image file using Structural Parsing for PDFs.
#     Includes metadata cleaning to prevent ChromaDB crashes.
#     """
#     try:
#         splits = []
        
#         # --- CASE 1: IMAGES (Requires LLM Transcription) ---
#         if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
#             logging.info("🖼️ Processing Image with LLM Vision...")
#             with open(file_path, "rb") as image_file:
#                 image_data = base64.b64encode(image_file.read()).decode("utf-8")
            
#             message = HumanMessage(
#                 content=[
#                     {"type": "text", "text": "Transcribe and describe this legal document image in detail. Capture all headers and clauses accurately."},
#                     {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
#                 ]
#             )
#             response = llm.invoke([message])
#             text_content = response.content
            
#             splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#             splits = splitter.create_documents([text_content])

#         # --- CASE 2: PDFs (Uses Unstructured Structural Chunking) ---
#         else:
#             logging.info("📄 Processing PDF with Structural Chunking...")
#             loader = UnstructuredLoader(
#                 file_path,
#                 chunking_strategy="by_title",
#                 max_characters=2000,
#                 new_after_n_chars=1500,
#                 combine_text_under_n_chars=500,
#             )
#             splits = loader.load()

#         # --- CRITICAL FIX: CLEAN METADATA ---
#         # ChromaDB cannot handle lists in metadata (like ['eng']). 
#         # This function filters them out.
#         if splits:
#             splits = filter_complex_metadata(splits)  # <--- FIX APPLIED HERE

#             vectorstore = get_vector_store()
#             vectorstore.add_documents(splits)
#             logging.info(f"✅ Successfully added {len(splits)} structural chunks to DB.")
#             return len(splits)
        
#         logging.warning("⚠️ No text chunks were created from the document.")
#         return 0

#     except Exception as e:
#         logging.error(f"❌ Error processing document: {str(e)}")
#         raise e

#     finally:
#         # Secure Cleanup
#         if os.path.exists(file_path):
#             os.remove(file_path)
#             logging.info(f"Deleted secure file: {file_path}")
            
# def refine_chunks(docs):
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=800,
#         chunk_overlap=100,
#         separators=["\n(a)", "\n(b)", "\n(c)", "\n(d)", "\n\n"]
#     )
#     refined = []
#     for doc in docs:
#         refined.extend(splitter.create_documents([doc.page_content], metadata=doc.metadata))
#     return refined
