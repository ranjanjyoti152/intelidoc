"""
InteliDoc RAG Pipeline - Docling Client Service
Client for communicating with the Docling document processing service.
"""

import httpx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


class ProcessedChunk(BaseModel):
    """Represents a processed text chunk from a document."""
    content: str
    page_number: Optional[int] = None
    chunk_index: int
    metadata: Optional[Dict[str, Any]] = None


class DoclingClient:
    """Client for the Docling document processing service."""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.docling_host
        self.timeout = httpx.Timeout(300.0, connect=10.0)  # 5 min for processing
    
    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> List[ProcessedChunk]:
        """
        Send a document to the Docling service for processing.
        
        Args:
            file_content: Raw bytes of the document file
            filename: Original filename
            content_type: MIME type of the document
            chunk_size: Size of text chunks (default from settings)
            chunk_overlap: Overlap between chunks (default from settings)
            
        Returns:
            List of processed text chunks
        """
        chunk_size = chunk_size or settings.chunk_size
        chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                files = {"file": (filename, file_content, content_type)}
                data = {
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                }
                
                response = await client.post(
                    f"{self.base_url}/process",
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                
                result = response.json()
                chunks = [
                    ProcessedChunk(
                        content=chunk["content"],
                        page_number=chunk.get("page_number"),
                        chunk_index=idx,
                        metadata=chunk.get("metadata"),
                    )
                    for idx, chunk in enumerate(result.get("chunks", []))
                ]
                
                logger.info(f"Processed document '{filename}' into {len(chunks)} chunks")
                return chunks
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Docling service error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"Document processing failed: {e.response.text}")
            except httpx.RequestError as e:
                logger.error(f"Docling service connection error: {e}")
                raise RuntimeError(f"Could not connect to document processing service: {e}")
    
    async def health_check(self) -> bool:
        """Check if the Docling service is healthy."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
            except Exception as e:
                logger.warning(f"Docling health check failed: {e}")
                return False


# Singleton instance
_docling_client: Optional[DoclingClient] = None


def get_docling_client() -> DoclingClient:
    """Get the Docling client singleton."""
    global _docling_client
    if _docling_client is None:
        _docling_client = DoclingClient()
    return _docling_client
