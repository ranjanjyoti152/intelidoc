"""
InteliDoc RAG Pipeline - Document Management Routes
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid
import os
import logging
import aiofiles

from app.database import get_db
from app.schemas import (
    DocumentResponse,
    DocumentListResponse,
    UploadResponse,
)
from app.services.vector_store import VectorStore
from app.services.docling_client import get_docling_client
from app.services.embeddings import get_embedding_service
from app.config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()

UPLOAD_DIR = "/app/uploads"
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/markdown",
    "text/html",
}


async def process_document_task(
    document_id: int,
    file_path: str,
    original_filename: str,
    content_type: str,
):
    """
    Background task to process a document.
    - Sends to Docling for parsing and chunking
    - Generates embeddings for chunks
    - Stores in vector database
    """
    from app.database import get_db_session
    
    async with get_db_session() as session:
        vector_store = VectorStore(session)
        docling_client = get_docling_client()
        embedding_service = get_embedding_service()
        
        try:
            # Update status to processing
            await vector_store.update_document_status(document_id, "processing")
            
            # Read file content
            async with aiofiles.open(file_path, "rb") as f:
                file_content = await f.read()
            
            # Process document with Docling
            logger.info(f"Processing document {document_id} with Docling...")
            processed_chunks = await docling_client.process_document(
                file_content=file_content,
                filename=original_filename,
                content_type=content_type,
            )
            
            if not processed_chunks:
                await vector_store.update_document_status(
                    document_id, "failed", error_message="No text content extracted from document"
                )
                return
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(processed_chunks)} chunks...")
            texts = [chunk.content for chunk in processed_chunks]
            embeddings = embedding_service.embed_texts(texts)
            
            # Prepare chunk data
            chunks_data = [
                (
                    chunk.content,
                    embedding,
                    chunk.page_number,
                    chunk.metadata,
                )
                for chunk, embedding in zip(processed_chunks, embeddings)
            ]
            
            # Store chunks with embeddings
            chunk_count = await vector_store.store_chunks(document_id, chunks_data)
            
            # Get page count if available
            page_numbers = [c.page_number for c in processed_chunks if c.page_number]
            page_count = max(page_numbers) if page_numbers else None
            
            # Update document status
            await vector_store.update_document_status(
                document_id, "completed", page_count=page_count
            )
            
            logger.info(f"Document {document_id} processed successfully with {chunk_count} chunks")
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            await vector_store.update_document_status(
                document_id, "failed", error_message=str(e)
            )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document for processing.
    
    The document will be processed asynchronously:
    1. Parsed and chunked by Docling
    2. Embeddings generated for each chunk
    3. Stored in the vector database
    """
    # Validate file type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".bin"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Save file
    content = await file.read()
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    
    # Create document record
    vector_store = VectorStore(db)
    document = await vector_store.create_document(
        filename=unique_filename,
        original_filename=file.filename or "unknown",
        content_type=file.content_type,
        file_size=len(content),
    )
    await db.commit()
    
    # Queue background processing
    background_tasks.add_task(
        process_document_task,
        document.id,
        file_path,
        file.filename or "unknown",
        file.content_type or "application/octet-stream",
    )
    
    return UploadResponse(
        document_id=document.id,
        filename=file.filename or "unknown",
        status="pending",
        message="Document uploaded successfully. Processing started in background.",
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all documents with pagination."""
    vector_store = VectorStore(db)
    documents, total = await vector_store.list_documents(page, page_size, status)
    
    # Get chunk counts for each document
    document_responses = []
    for doc in documents:
        chunk_count = await vector_store.get_chunk_count(doc.id)
        response = DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            content_type=doc.content_type,
            file_size=doc.file_size,
            page_count=doc.page_count,
            status=doc.status,
            error_message=doc.error_message,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            chunk_count=chunk_count,
        )
        document_responses.append(response)
    
    return DocumentListResponse(
        documents=document_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get document details by ID."""
    vector_store = VectorStore(db)
    document = await vector_store.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    chunk_count = await vector_store.get_chunk_count(document_id)
    
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        original_filename=document.original_filename,
        content_type=document.content_type,
        file_size=document.file_size,
        page_count=document.page_count,
        status=document.status,
        error_message=document.error_message,
        created_at=document.created_at,
        updated_at=document.updated_at,
        chunk_count=chunk_count,
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and all its chunks."""
    vector_store = VectorStore(db)
    
    # Get document to check it exists and get filename
    document = await vector_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from database
    deleted = await vector_store.delete_document(document_id)
    await db.commit()
    
    # Try to delete file
    file_path = os.path.join(UPLOAD_DIR, document.filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"Could not delete file {file_path}: {e}")
    
    return {"message": f"Document {document_id} deleted successfully"}
