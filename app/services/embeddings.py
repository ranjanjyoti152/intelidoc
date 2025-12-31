"""
InteliDoc RAG Pipeline - Embedding Service
GPU-accelerated embedding generation using Sentence Transformers.
"""

import torch
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import logging
import numpy as np

from app.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating text embeddings using Sentence Transformers."""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embedding_model
        self.model: Optional[SentenceTransformer] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Embedding service will use device: {self.device}")
    
    def _load_model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"Model loaded successfully. Dimension: {self.model.get_sentence_embedding_dimension()}")
        return self.model
    
    def get_dimension(self) -> int:
        """Get the embedding dimension of the model."""
        model = self._load_model()
        return model.get_sentence_embedding_dimension()
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        model = self._load_model()
        embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of input texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        model = self._load_model()
        logger.info(f"Generating embeddings for {len(texts)} texts (batch_size={batch_size})")
        
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 10,
        )
        
        return embeddings.tolist()
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query text.
        Some models have different behavior for queries vs documents.
        
        Args:
            query: Query text to embed
            
        Returns:
            List of floats representing the query embedding
        """
        # For most sentence-transformers models, query and document embedding are the same
        # For specialized models like BGE, you might add a prefix like "query: "
        return self.embed_text(query)
    
    async def health_check(self) -> bool:
        """Check if the embedding service is healthy."""
        try:
            # Try to load model and generate a test embedding
            test_embedding = self.embed_text("test")
            return len(test_embedding) == settings.embedding_dimension
        except Exception as e:
            logger.error(f"Embedding service health check failed: {e}")
            return False


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
