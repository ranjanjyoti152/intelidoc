"""
InteliDoc RAG Pipeline - Vector Store Service
PostgreSQL pgvector operations for storing and retrieving embeddings.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, text
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
import logging

from app.models import Document, DocumentChunk
from app.schemas import SearchResult
from app.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStore:
    """Service for vector storage and similarity search operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_document(
        self,
        filename: str,
        original_filename: str,
        content_type: Optional[str] = None,
        file_size: Optional[int] = None,
    ) -> Document:
        """
        Create a new document record.
        
        Args:
            filename: Stored filename
            original_filename: Original uploaded filename
            content_type: MIME type
            file_size: File size in bytes
            
        Returns:
            Created Document instance
        """
        document = Document(
            filename=filename,
            original_filename=original_filename,
            content_type=content_type,
            file_size=file_size,
            status="pending",
        )
        self.session.add(document)
        await self.session.flush()
        logger.info(f"Created document record: id={document.id}, filename={filename}")
        return document
    
    async def update_document_status(
        self,
        document_id: int,
        status: str,
        page_count: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update document processing status."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        document = result.scalar_one_or_none()
        
        if document:
            document.status = status
            if page_count is not None:
                document.page_count = page_count
            if error_message is not None:
                document.error_message = error_message
            await self.session.flush()
    
    async def store_chunks(
        self,
        document_id: int,
        chunks: List[Tuple[str, List[float], Optional[int], Optional[dict]]],
    ) -> int:
        """
        Store document chunks with their embeddings.
        
        Args:
            document_id: ID of the parent document
            chunks: List of tuples (content, embedding, page_number, metadata)
            
        Returns:
            Number of chunks stored
        """
        chunk_objects = []
        for idx, (content, embedding, page_number, chunk_metadata) in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=idx,
                content=content,
                embedding=embedding,
                page_number=page_number,
                chunk_metadata=chunk_metadata,
            )
            chunk_objects.append(chunk)
        
        self.session.add_all(chunk_objects)
        await self.session.flush()
        logger.info(f"Stored {len(chunk_objects)} chunks for document {document_id}")
        return len(chunk_objects)
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        document_ids: Optional[List[int]] = None,
    ) -> List[SearchResult]:
        """
        Perform similarity search using cosine distance.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            document_ids: Optional filter to specific documents
            
        Returns:
            List of SearchResult with similarity scores
        """
        # Build the similarity search query using pgvector's cosine distance
        # 1 - cosine_distance = cosine_similarity
        similarity_expr = 1 - DocumentChunk.embedding.cosine_distance(query_embedding)
        
        stmt = (
            select(
                DocumentChunk.id,
                DocumentChunk.document_id,
                DocumentChunk.content,
                DocumentChunk.page_number,
                Document.original_filename,
                similarity_expr.label("similarity_score"),
            )
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.status == "completed")
            .order_by(similarity_expr.desc())
            .limit(top_k)
        )
        
        # Filter by document IDs if specified
        if document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))
        
        result = await self.session.execute(stmt)
        rows = result.fetchall()
        
        search_results = [
            SearchResult(
                chunk_id=row.id,
                document_id=row.document_id,
                document_filename=row.original_filename,
                content=row.content,
                page_number=row.page_number,
                similarity_score=float(row.similarity_score),
            )
            for row in rows
        ]
        
        logger.info(f"Similarity search returned {len(search_results)} results")
        return search_results
    
    async def get_document(self, document_id: int) -> Optional[Document]:
        """Get a document by ID."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_document_with_chunks(self, document_id: int) -> Optional[Document]:
        """Get a document with its chunks."""
        stmt = (
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.id == document_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[List[Document], int]:
        """
        List documents with pagination.
        
        Returns:
            Tuple of (documents list, total count)
        """
        # Count query
        count_stmt = select(func.count(Document.id))
        if status:
            count_stmt = count_stmt.where(Document.status == status)
        total = (await self.session.execute(count_stmt)).scalar()
        
        # List query
        stmt = (
            select(Document)
            .order_by(Document.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        if status:
            stmt = stmt.where(Document.status == status)
        
        result = await self.session.execute(stmt)
        documents = result.scalars().all()
        
        return list(documents), total
    
    async def delete_document(self, document_id: int) -> bool:
        """Delete a document and all its chunks."""
        stmt = delete(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
    
    async def get_chunk_count(self, document_id: int) -> int:
        """Get the number of chunks for a document."""
        stmt = select(func.count(DocumentChunk.id)).where(
            DocumentChunk.document_id == document_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
