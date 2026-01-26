"""
Configuration
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Sistema de configuração centralizado usando variáveis de ambiente.
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from common.exceptions import ConfigurationError
from common.types import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_LLM_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_RETRIEVAL_K,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_PERSIST_DIRECTORY
)


@dataclass
class Config:
    """
    Configuração da aplicação.
    
    Carrega configurações de variáveis de ambiente e fornece valores padrão.
    """
    
    # OpenAI
    openai_api_key: str
    llm_model: str = DEFAULT_LLM_MODEL
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    
    # Chunking
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    
    # ChromaDB
    collection_name: str = DEFAULT_COLLECTION_NAME
    persist_directory: str = DEFAULT_PERSIST_DIRECTORY
    
    # Agent
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    retrieval_k: int = DEFAULT_RETRIEVAL_K
    verbose: bool = True
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """
        Cria configuração a partir de variáveis de ambiente.
        
        Args:
            env_file: Caminho para arquivo .env (opcional)
            
        Returns:
            Instância de Config
            
        Raises:
            ConfigurationError: Se configuração obrigatória estiver faltando
        """
        # Carrega .env se fornecido
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv(override=True)  # Carrega .env padrão
        
        # OpenAI API Key é obrigatória
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY não encontrada nas variáveis de ambiente.\n"
                "Crie um arquivo .env com: OPENAI_API_KEY=sk-..."
            )
        
        # Carrega outras configs com valores padrão
        return cls(
            openai_api_key=api_key,
            llm_model=os.getenv("OPENAI_MODEL", DEFAULT_LLM_MODEL),
            embedding_model=os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
            temperature=float(os.getenv("TEMPERATURE", DEFAULT_TEMPERATURE)),
            chunk_size=int(os.getenv("CHUNK_SIZE", DEFAULT_CHUNK_SIZE)),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP)),
            collection_name=os.getenv("COLLECTION_NAME", DEFAULT_COLLECTION_NAME),
            persist_directory=os.getenv("PERSIST_DIRECTORY", DEFAULT_PERSIST_DIRECTORY),
            max_iterations=int(os.getenv("MAX_ITERATIONS", DEFAULT_MAX_ITERATIONS)),
            retrieval_k=int(os.getenv("RETRIEVAL_K", DEFAULT_RETRIEVAL_K)),
            verbose=os.getenv("VERBOSE", "true").lower() == "true"
        )
    
    def validate(self) -> None:
        """
        Valida configurações.
        
        Raises:
            ConfigurationError: Se alguma configuração for inválida
        """
        # Valida API Key
        if not self.openai_api_key.startswith("sk-"):
            raise ConfigurationError(
                "OPENAI_API_KEY inválida (deve começar com 'sk-')"
            )
        
        # Valida chunk size
        if self.chunk_size < 100 or self.chunk_size > 2000:
            raise ConfigurationError(
                f"chunk_size deve estar entre 100 e 2000. Valor: {self.chunk_size}"
            )
        
        # Valida chunk overlap
        if self.chunk_overlap >= self.chunk_size:
            raise ConfigurationError(
                f"chunk_overlap ({self.chunk_overlap}) deve ser menor que "
                f"chunk_size ({self.chunk_size})"
            )
        
        # Valida temperature
        if not 0 <= self.temperature <= 2:
            raise ConfigurationError(
                f"temperature deve estar entre 0 e 2. Valor: {self.temperature}"
            )
    
    def __str__(self) -> str:
        """Representação string da configuração (sem expor API key completa)."""
        return f"""
Config:
  OpenAI:
    API Key: {self.openai_api_key[:10]}...
    LLM Model: {self.llm_model}
    Embedding Model: {self.embedding_model}
    Temperature: {self.temperature}
  
  Chunking:
    Chunk Size: {self.chunk_size}
    Chunk Overlap: {self.chunk_overlap}
  
  ChromaDB:
    Collection: {self.collection_name}
    Persist Dir: {self.persist_directory}
  
  Agent:
    Max Iterations: {self.max_iterations}
    Retrieval K: {self.retrieval_k}
    Verbose: {self.verbose}
        """.strip()
