"""
InteliDoc RAG Pipeline - FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.database import init_db, close_db
from app.routes import documents, query, websocket, stats


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    """
    # Startup
    logger.info("Starting InteliDoc RAG Pipeline...")
    try:
        await init_db()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Pre-load embedding model
    try:
        from app.services.embeddings import get_embedding_service
        embedding_service = get_embedding_service()
        dim = embedding_service.get_dimension()
        logger.info(f"Embedding model loaded (dimension: {dim})")
    except Exception as e:
        logger.warning(f"Could not pre-load embedding model: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down InteliDoc RAG Pipeline...")
    await close_db()
    logger.info("Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title="InteliDoc RAG Pipeline",
    description="""
## Retrieval-Augmented Generation Pipeline

Upload documents, process them with Docling, store embeddings in PostgreSQL with pgvector,
and query them using natural language with LLM-powered responses.

### Features
- 📄 **Document Upload**: Support for PDF, DOCX, TXT, HTML, Markdown
- 🔍 **Vector Search**: Fast similarity search using pgvector HNSW indexes
- 🤖 **RAG Queries**: Ask questions and get AI-generated answers with source citations
- 🚀 **GPU Accelerated**: Document processing and embeddings leverage GPU

### Quick Start
1. Upload documents via `/documents/upload`
2. Check processing status via `/documents`
3. Query your documents via `/query`
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(websocket.router)
app.include_router(stats.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "InteliDoc RAG Pipeline",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
