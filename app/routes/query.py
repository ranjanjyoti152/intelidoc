"""
InteliDoc RAG Pipeline - Query and Search Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import get_db
from app.schemas import (
    QueryRequest,
    QueryResponse,
    SearchResponse,
    HealthStatus,
)
from app.services.vector_store import VectorStore
from app.services.rag_chain import RAGChain
from app.services.embeddings import get_embedding_service
from app.services.docling_client import get_docling_client
from app.config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(tags=["query"])
settings = get_settings()


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ask a question about your documents.
    
    This performs RAG (Retrieval-Augmented Generation):
    1. Retrieves relevant document chunks using vector similarity search
    2. Sends the context and question to the LLM
    3. Returns the generated answer with source references
    """
    vector_store = VectorStore(db)
    rag_chain = RAGChain(vector_store)
    
    try:
        response = await rag_chain.query(
            query=request.query,
            top_k=request.top_k,
            document_ids=request.document_ids,
        )
        return response
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your query")


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Search for relevant document chunks without LLM generation.
    
    This performs only the retrieval step of RAG:
    - Returns the most similar document chunks to your query
    - Useful for exploring what information is available
    """
    vector_store = VectorStore(db)
    rag_chain = RAGChain(vector_store)
    
    try:
        results = await rag_chain.search_only(
            query=request.query,
            top_k=request.top_k,
            document_ids=request.document_ids,
        )
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while searching")


@router.get("/health", response_model=HealthStatus)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Check the health status of all services.
    """
    from sqlalchemy import text
    
    status = "healthy"
    details = {}
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
        status = "degraded"
    
    # Check LLM provider
    try:
        from app.services.rag_chain import RAGChain
        vector_store = VectorStore(db)
        rag_chain = RAGChain(vector_store)
        llm_ok = await rag_chain.health_check_llm()
        provider_info = f"{settings.llm_provider}:{rag_chain.llm_provider.model_name}"
        llm_status = f"connected ({provider_info})" if llm_ok else f"not responding ({provider_info})"
        if not llm_ok:
            status = "degraded"
            if settings.llm_provider == "ollama":
                details["llm_note"] = f"Model {settings.ollama_model} may need to be pulled"
    except ValueError as e:
        llm_status = f"config error: {e}"
        status = "degraded"
    except Exception as e:
        llm_status = f"error: {e}"
        status = "degraded"
    
    # Check Docling
    try:
        docling_client = get_docling_client()
        docling_ok = await docling_client.health_check()
        docling_status = "connected" if docling_ok else "not responding"
        if not docling_ok:
            status = "degraded"
    except Exception as e:
        docling_status = f"error: {e}"
        status = "degraded"
    
    # Check embedding model
    try:
        embedding_service = get_embedding_service()
        embedding_ok = await embedding_service.health_check()
        embedding_status = f"loaded ({settings.embedding_model})" if embedding_ok else "not loaded"
        if not embedding_ok:
            status = "degraded"
    except Exception as e:
        embedding_status = f"error: {e}"
        status = "degraded"
    
    return HealthStatus(
        status=status,
        database=db_status,
        ollama=llm_status,  # Kept as 'ollama' for API compatibility
        docling=docling_status,
        embedding_model=embedding_status,
        details=details if details else None,
    )
