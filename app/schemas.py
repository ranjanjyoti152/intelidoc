"""
InteliDoc RAG Pipeline - Pydantic Schemas for API
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Document Schemas
class DocumentBase(BaseModel):
    """Base schema for document."""
    original_filename: str


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    pass


class DocumentChunkResponse(BaseModel):
    """Schema for document chunk response."""
    id: int
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    similarity_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: int
    filename: str
    original_filename: str
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    chunk_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for paginated document list."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


# Query Schemas
class QueryRequest(BaseModel):
    """Schema for RAG query request."""
    query: str = Field(..., min_length=1, max_length=2000, description="The question to ask")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of relevant chunks to retrieve")
    document_ids: Optional[List[int]] = Field(default=None, description="Filter to specific documents")


class SearchResult(BaseModel):
    """Schema for a single search result."""
    chunk_id: int
    document_id: int
    document_filename: str
    content: str
    page_number: Optional[int] = None
    similarity_score: float


class SearchResponse(BaseModel):
    """Schema for vector search response."""
    query: str
    results: List[SearchResult]
    total_results: int


class QueryResponse(BaseModel):
    """Schema for RAG query response."""
    query: str
    answer: str
    sources: List[SearchResult]
    model_used: str


# Health Check Schemas
class HealthStatus(BaseModel):
    """Schema for service health status."""
    status: str
    database: str
    ollama: str
    docling: str
    embedding_model: str
    details: Optional[dict] = None


# Upload Response
class UploadResponse(BaseModel):
    """Schema for upload response."""
    document_id: int
    filename: str
    status: str
    message: str
