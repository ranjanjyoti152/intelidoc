"""
InteliDoc RAG Pipeline - RAG Chain Service
Retrieval-Augmented Generation with multi-provider LLM support.
Supports: Ollama (local), OpenAI-compatible APIs, Google Gemini
"""

import httpx
from typing import List, Optional, Protocol
from abc import ABC, abstractmethod
import logging
import json

from app.config import get_settings
from app.schemas import SearchResult, QueryResponse
from app.services.embeddings import get_embedding_service
from app.services.vector_store import VectorStore


logger = logging.getLogger(__name__)
settings = get_settings()


# RAG Prompt Template
RAG_PROMPT_TEMPLATE = """You are a helpful AI assistant that answers questions based on the provided context.
Use the following pieces of context to answer the question at the end.
If you don't know the answer based on the context, just say that you don't know.
Don't try to make up an answer. Be concise and accurate.

Context:
{context}

Question: {question}

Answer:"""


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the model name."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self):
        self.host = settings.ollama_host
        self._model_name = settings.ollama_model
        self.timeout = httpx.Timeout(120.0, connect=10.0)
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self._model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 1024,
                    },
                },
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
    
    async def health_check(self) -> bool:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            try:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
            except Exception:
                return False


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible API provider (works with OpenAI, Azure, Groq, Together, vLLM, etc.)."""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.api_base = settings.openai_api_base.rstrip("/")
        self._model_name = settings.openai_model
        self.timeout = httpx.Timeout(120.0, connect=10.0)
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model_name,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
    
    async def health_check(self) -> bool:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            try:
                response = await client.get(
                    f"{self.api_base}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code == 200
            except Exception:
                return False


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self._model_name = settings.gemini_model
        self.api_base = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = httpx.Timeout(120.0, connect=10.0)
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider")
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/models/{self._model_name}:generateContent",
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {"parts": [{"text": prompt}]}
                    ],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 1024,
                    },
                },
            )
            response.raise_for_status()
            result = response.json()
            # Extract text from Gemini response
            candidates = result.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            return ""
    
    async def health_check(self) -> bool:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            try:
                response = await client.get(
                    f"{self.api_base}/models",
                    params={"key": self.api_key},
                )
                return response.status_code == 200
            except Exception:
                return False


def get_llm_provider() -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    provider = settings.llm_provider.lower()
    
    if provider == "ollama":
        return OllamaProvider()
    elif provider == "openai":
        return OpenAIProvider()
    elif provider == "gemini":
        return GeminiProvider()
    else:
        logger.warning(f"Unknown provider '{provider}', falling back to Ollama")
        return OllamaProvider()


class RAGChain:
    """Service for performing Retrieval-Augmented Generation."""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.embedding_service = get_embedding_service()
        self.llm_provider = get_llm_provider()
        self.timeout = httpx.Timeout(120.0, connect=10.0)
    
    async def query(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[int]] = None,
    ) -> QueryResponse:
        """
        Perform RAG query: retrieve relevant context and generate answer.
        
        Args:
            query: User's question
            top_k: Number of relevant chunks to retrieve
            document_ids: Optional filter to specific documents
            
        Returns:
            QueryResponse with answer and sources
        """
        # Step 1: Generate query embedding
        logger.info(f"Generating embedding for query: {query[:50]}...")
        query_embedding = self.embedding_service.embed_query(query)
        
        # Step 2: Retrieve relevant chunks
        logger.info(f"Retrieving top {top_k} relevant chunks...")
        search_results = await self.vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
        )
        
        if not search_results:
            return QueryResponse(
                query=query,
                answer="I couldn't find any relevant information in the documents to answer your question.",
                sources=[],
                model_used=self.llm_provider.model_name,
            )
        
        # Step 3: Build context from retrieved chunks
        context_parts = []
        for i, result in enumerate(search_results, 1):
            source_info = f"[Source {i}: {result.document_filename}"
            if result.page_number:
                source_info += f", Page {result.page_number}"
            source_info += "]"
            context_parts.append(f"{source_info}\n{result.content}")
        
        context = "\n\n".join(context_parts)
        
        # Step 4: Generate answer using LLM
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=query)
        logger.info(f"Generating answer using {self.llm_provider.model_name} ({settings.llm_provider})...")
        
        try:
            answer = await self.llm_provider.generate(prompt)
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"LLM generation failed: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"LLM connection error: {e}")
            raise RuntimeError(f"Could not connect to LLM service: {e}")
        
        return QueryResponse(
            query=query,
            answer=answer,
            sources=search_results,
            model_used=f"{settings.llm_provider}:{self.llm_provider.model_name}",
        )
    
    async def search_only(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[int]] = None,
    ) -> List[SearchResult]:
        """
        Perform vector search without LLM generation.
        
        Args:
            query: Search query
            top_k: Number of results
            document_ids: Optional filter
            
        Returns:
            List of SearchResult
        """
        query_embedding = self.embedding_service.embed_query(query)
        return await self.vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
        )
    
    async def health_check_llm(self) -> bool:
        """Check if the LLM provider is responsive."""
        try:
            return await self.llm_provider.health_check()
        except Exception as e:
            logger.warning(f"LLM health check failed: {e}")
            return False
