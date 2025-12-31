"""
InteliDoc - Docling Document Processing Service
Standalone microservice for document parsing and chunking using Docling.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import tempfile
import os

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Pydantic models
class ChunkResult(BaseModel):
    """A processed text chunk."""
    content: str
    page_number: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ProcessResponse(BaseModel):
    """Response from document processing."""
    filename: str
    total_chunks: int
    total_pages: Optional[int] = None
    chunks: List[ChunkResult]


# Create FastAPI app
app = FastAPI(
    title="Docling Document Processing Service",
    description="GPU-accelerated document processing with Docling",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global document converter (lazy initialized)
_converter: Optional[DocumentConverter] = None


def get_converter() -> DocumentConverter:
    """Get or create the document converter."""
    global _converter
    if _converter is None:
        logger.info("Initializing Docling DocumentConverter...")
        
        # Configure pipeline options for PDF processing
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True  # Enable OCR for scanned documents
        pipeline_options.do_table_structure = True  # Extract table structure
        
        _converter = DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.HTML,
                InputFormat.PPTX,
                InputFormat.IMAGE,
                InputFormat.MD,
            ],
        )
        logger.info("DocumentConverter initialized successfully")
    
    return _converter


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between consecutive chunks
    
    Returns:
        List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    prev_end = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at a sentence or word boundary
        if end < len(text):
            # Look for sentence boundary
            for sep in ['. ', '.\n', '\n\n', '\n', ' ']:
                last_sep = text.rfind(sep, start, end)
                if last_sep > start:
                    end = last_sep + len(sep)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start for next chunk with overlap
        prev_end = end
        start = end - chunk_overlap if end < len(text) else end
        
        # Prevent infinite loop
        if start <= prev_end - chunk_size:
            start = end
    
    return chunks


@app.post("/process", response_model=ProcessResponse)
async def process_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(default=500),
    chunk_overlap: int = Form(default=50),
):
    """
    Process a document and return text chunks.
    
    The document is parsed using Docling, which supports:
    - PDF (with OCR for scanned documents)
    - DOCX
    - HTML
    - PPTX
    - Images
    - Markdown
    
    Text is then split into overlapping chunks for RAG processing.
    """
    logger.info(f"Processing document: {file.filename} ({file.content_type})")
    
    # Save to temp file
    suffix = os.path.splitext(file.filename)[1] if file.filename else ""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Process with Docling
        converter = get_converter()
        result = converter.convert(tmp_path)
        
        # Get document as markdown
        doc = result.document
        full_text = doc.export_to_markdown()
        
        # Get page information if available
        total_pages = None
        if hasattr(doc, 'pages') and doc.pages:
            total_pages = len(doc.pages)
        
        # Chunk the text
        text_chunks = chunk_text(full_text, chunk_size, chunk_overlap)
        
        # Create chunk results
        chunks = []
        for idx, chunk_text_content in enumerate(text_chunks):
            # Try to determine page number (simplified - assumes sequential pages)
            page_num = None
            if total_pages:
                # Estimate page based on position in document
                position_ratio = idx / max(len(text_chunks), 1)
                page_num = int(position_ratio * total_pages) + 1
            
            chunks.append(ChunkResult(
                content=chunk_text_content,
                page_number=page_num,
                metadata={
                    "chunk_index": idx,
                    "source_filename": file.filename,
                },
            ))
        
        logger.info(f"Document processed: {len(chunks)} chunks from {total_pages or 'unknown'} pages")
        
        return ProcessResponse(
            filename=file.filename or "unknown",
            total_chunks=len(chunks),
            total_pages=total_pages,
            chunks=chunks,
        )
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")
    
    finally:
        # Cleanup temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Try to get converter to verify initialization works
        get_converter()
        return {"status": "healthy", "service": "docling"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Docling Document Processing",
        "version": "1.0.0",
        "endpoints": {
            "process": "/process",
            "health": "/health",
        },
    }
