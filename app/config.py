"""
InteliDoc RAG Pipeline - Configuration Management
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Optional, Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "intelidoc"
    postgres_password: str = "intelidoc_secret"
    postgres_db: str = "intelidoc"
    
    # LLM Provider Selection
    llm_provider: Literal["ollama", "openai", "gemini"] = "ollama"
    
    # Ollama Configuration
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    # OpenAI-Compatible API Configuration
    openai_api_key: Optional[str] = None
    openai_api_base: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    
    # Google Gemini Configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # Docling Service Configuration
    docling_host: str = "http://localhost:8001"
    
    # Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # RAG Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 9060
    
    # Legacy support: map old llm_model to appropriate provider model
    llm_model: Optional[str] = Field(default=None, description="Deprecated: use provider-specific model settings")
    
    @property
    def active_llm_model(self) -> str:
        """Get the active LLM model based on provider."""
        if self.llm_model:
            return self.llm_model  # Legacy support
        if self.llm_provider == "ollama":
            return self.ollama_model
        elif self.llm_provider == "openai":
            return self.openai_model
        elif self.llm_provider == "gemini":
            return self.gemini_model
        return self.ollama_model
    
    @property
    def database_url(self) -> str:
        """Construct async database URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def sync_database_url(self) -> str:
        """Construct sync database URL for migrations."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
