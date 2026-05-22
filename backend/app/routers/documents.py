import os
import shutil
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.dependencies import get_current_user
from app.services.db import db_save_document_chunks
from app.services.embeddings import embedding_service

router = APIRouter()

import tempfile

# Setup a temporary directory for uploaded PDFs
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "f-ai-uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    chat_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    from app.services.db import db_create_chat
    
    # If no chat_id is provided, create a new chat using the filename as the title
    final_chat_id = chat_id
    if not final_chat_id:
        new_chat = db_create_chat(current_user["id"], f"Document: {file.filename}")
        final_chat_id = new_chat["id"]

    # 1. Save file temporarily to disk (PyPDFLoader requires a filepath)
    file_path = os.path.join(UPLOAD_DIR, f"{final_chat_id}_{file.filename}")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Load the PDF using LangChain
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        
        # 2.5 Word count limitation check
        total_text = " ".join([doc.page_content for doc in docs])
        word_count = len(total_text.split())
        
        MAX_WORDS = 10000
        if word_count > MAX_WORDS:
            raise HTTPException(
                status_code=400, 
                detail=f"PDF is too large. The document contains {word_count} words, which exceeds the limit of {MAX_WORDS} words."
            )
        
        # 3. Split the text into manageable chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(docs)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not extract text from the PDF.")

        # 4. Generate embeddings and prepare database insertion payload
        db_chunks = []
        for chunk in chunks:
            content = chunk.page_content
            # Generate the 384-dimensional vector using our existing local model
            embedding = embedding_service.generate_embedding(content)
            
            db_chunks.append({
                "chat_id": final_chat_id,
                "content": content,
                "embedding": embedding
            })
            
        # 5. Save chunks to Supabase
        success = db_save_document_chunks(final_chat_id, db_chunks)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save document to the database.")

        return {
            "status": "success",
            "message": f"Successfully processed {len(chunks)} chunks from {file.filename}.",
            "chat_id": final_chat_id
        }

    except HTTPException:
        raise  # re-raise validation errors (word limit, no text, etc.) as-is
    except Exception as e:
        print(f"Document Upload Error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the document.")
    finally:
        # Cleanup temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
