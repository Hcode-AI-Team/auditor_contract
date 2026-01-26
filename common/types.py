"""
Tipos e Constantes
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Define tipos, enums, protocols e constantes usadas em toda a aplicação.
"""

from enum import Enum
from typing import Protocol, List, Optional, Dict, Any, TypeVar, Generic, Callable, Awaitable
from dataclasses import dataclass
from abc import ABC, abstractmethod


# ============================================================================
# ENUMS
# ============================================================================

class DocumentType(str, Enum):
    """Tipos de documentos suportados."""
    PDF = "pdf"
    TXT = "txt"


class ChunkingStrategy(str, Enum):
    """Estratégias de chunking disponíveis."""
    RECURSIVE = "recursive"
    CHARACTER = "character"
    SEMANTIC = "semantic"


class RiskLevel(str, Enum):
    """Níveis de risco legal."""
    BAIXO = "Baixo"
    MEDIO = "Médio"
    ALTO = "Alto"


class AgentStatus(str, Enum):
    """Status do agente durante execução."""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    FINISHED = "finished"
    ERROR = "error"


# ============================================================================
# PROTOCOLS - Interfaces para tipagem estrutural
# ============================================================================

class EmbeddingsProtocol(Protocol):
    """Protocol para modelos de embeddings."""
    
    def embed_query(self, text: str) -> List[float]:
        """Gera embedding para um texto de query."""
        ...
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para múltiplos documentos."""
        ...
    
    async def aembed_query(self, text: str) -> List[float]:
        """Gera embedding para um texto de query (async)."""
        ...
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para múltiplos documentos (async)."""
        ...


class LLMProtocol(Protocol):
    """Protocol para modelos de linguagem."""
    
    def invoke(self, input: Any) -> Any:
        """Invoca o LLM com input."""
        ...
    
    async def ainvoke(self, input: Any) -> Any:
        """Invoca o LLM com input (async)."""
        ...


class VectorStoreProtocol(Protocol):
    """Protocol para vector stores."""
    
    def similarity_search(self, query: str, k: int = 4) -> List[Any]:
        """Busca por similaridade."""
        ...
    
    def similarity_search_with_score(self, query: str, k: int = 4) -> List[tuple[Any, float]]:
        """Busca por similaridade com scores."""
        ...
    
    def add_documents(self, documents: List[Any]) -> List[str]:
        """Adiciona documentos."""
        ...


class ChunkingProtocol(Protocol):
    """Protocol para estratégias de chunking."""
    
    def split(self, text: str) -> List[str]:
        """Divide texto em chunks."""
        ...
    
    def split_documents(self, documents: List[Any]) -> List[Any]:
        """Divide documentos em chunks."""
        ...


class DocumentLoaderProtocol(Protocol):
    """Protocol para document loaders."""
    
    def load(self) -> List[Any]:
        """Carrega documentos."""
        ...


# ============================================================================
# TYPES - Type aliases e generics
# ============================================================================

# Type para funções de callback
CallbackFn = Callable[[str], None]
AsyncCallbackFn = Callable[[str], Awaitable[None]]

# Type para resultado de busca
SearchResult = tuple[Any, float]  # (documento, score)
SearchResults = List[SearchResult]

# Type para metadados de documento
DocumentMetadata = Dict[str, Any]

# Type genérico para resultado de operações
T = TypeVar('T')


@dataclass
class Result(Generic[T]):
    """Resultado de uma operação com sucesso/erro."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    @classmethod
    def ok(cls, data: T) -> 'Result[T]':
        """Cria resultado de sucesso."""
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str, details: Optional[Dict[str, Any]] = None) -> 'Result[T]':
        """Cria resultado de falha."""
        return cls(success=False, error=error, details=details)


@dataclass
class AgentStep:
    """Representa um passo na execução do agente."""
    thought: str
    action: Optional[str] = None
    action_input: Optional[str] = None
    observation: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class AnalysisResult:
    """Resultado completo de uma análise de contrato."""
    output: str
    intermediate_steps: List[AgentStep]
    metadata: Optional[Dict[str, Any]] = None
    duration_seconds: float = 0.0
    tokens_used: int = 0
    tool_calls: int = 0


# ============================================================================
# CONSTANTES
# ============================================================================

# Chunking
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50

# OpenAI Models
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_LLM_MODEL = "gpt-4o"  # Atualizado para modelo mais recente
DEFAULT_TEMPERATURE = 0

# Agent
DEFAULT_MAX_ITERATIONS = 10
DEFAULT_RETRIEVAL_K = 3

# ChromaDB
DEFAULT_COLLECTION_NAME = "contratos"
DEFAULT_PERSIST_DIRECTORY = "./chroma_db"

# Timeouts (segundos)
OPENAI_TIMEOUT = 60
CHROMADB_TIMEOUT = 30
DEFAULT_REQUEST_TIMEOUT = 120

# Limites
MAX_CHUNK_SIZE = 2000
MIN_CHUNK_SIZE = 100
MAX_RETRIES = 3
MAX_TOKENS_PER_REQUEST = 4096

# Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_TOKENS_PER_MINUTE = 150000


# ============================================================================
# ABSTRACT BASE CLASSES - Para herança
# ============================================================================

class BaseAdapter(ABC):
    """Classe base abstrata para todos os adapters."""
    
    @abstractmethod
    def health_check(self) -> bool:
        """Verifica se o adapter está saudável."""
        pass
    
    @abstractmethod
    async def ahealth_check(self) -> bool:
        """Verifica se o adapter está saudável (async)."""
        pass


class BaseRepository(ABC):
    """Classe base abstrata para repositórios."""
    
    @abstractmethod
    def save(self, entity: Any) -> str:
        """Salva entidade e retorna ID."""
        pass
    
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[Any]:
        """Busca entidade por ID."""
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        """Remove entidade por ID."""
        pass