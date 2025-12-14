# backend/ai/document_processor.py
import os
import base64
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import HumanMessage
from backend.engine.core import llm
from backend.engine.vector_store import get_vector_store

def process_document(file_path: str):
    """
    Processes a PDF or Image file:
    1. Transcribes images if needed.
    2. Splits text into chunks.
    3. Saves chunks to Vector Store.
    4. Securely deletes the original file.
    """
    try:
        splits = []
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Image handling
            with open(file_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": "Transcribe and describe this legal document image in detail."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            )
            response = llm.invoke([message])
            text_content = response.content
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = splitter.create_documents([text_content])
        else:
            # PDF handling
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = splitter.split_documents(docs)

        # Add to Database
        vectorstore = get_vector_store()
        vectorstore.add_documents(splits)
        return len(splits)

    finally:
        # Secure Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Deleted secure file: {file_path}")