"""
Common Layer - Código Compartilhado
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Este módulo contém código compartilhado por toda a aplicação:
- Exceções customizadas
- Tipos e constantes
- Logging estruturado
- Sistema de métricas
"""

from .exceptions import (
    AuditorError,
    ConfigurationError,
    DocumentLoadError,
    VectorStoreError,
    AgentError,
    EmbeddingError,
    LLMError,
    ValidationError,
    TimeoutError,
    RateLimitError,
)
from .types import (
    ChunkingStrategy,
    DocumentType,
    RiskLevel,
    AgentStatus,
    EmbeddingsProtocol,
    LLMProtocol,
    VectorStoreProtocol,
    Result,
    AgentStep,
    AnalysisResult,
)
from .logging import (
    get_logger,
    setup_logging,
    set_context,
    clear_context,
    LogContext,
    log_execution_time,
)
from .metrics import (
    metrics,
    MetricsCollector,
    AuditorMetrics,
    track_metrics,
)
from .retry import (
    retry_with_backoff,
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitState,
    RetryConfig,
    CircuitBreakerConfig,
    get_circuit_breaker,
    RETRY_CONFIG_OPENAI,
    RETRY_CONFIG_CHROMADB,
)
from .cache import (
    EmbeddingCache,
    InMemoryCache,
    FileCache,
    CacheEntry,
    CacheStats,
    get_embedding_cache,
    cached_embedding,
)

__all__ = [
    # Exceptions
    "AuditorError",
    "ConfigurationError",
    "DocumentLoadError",
    "VectorStoreError",
    "AgentError",
    "EmbeddingError",
    "LLMError",
    "ValidationError",
    "TimeoutError",
    "RateLimitError",
    # Types
    "ChunkingStrategy",
    "DocumentType",
    "RiskLevel",
    "AgentStatus",
    "EmbeddingsProtocol",
    "LLMProtocol",
    "VectorStoreProtocol",
    "Result",
    "AgentStep",
    "AnalysisResult",
    # Logging
    "get_logger",
    "setup_logging",
    "set_context",
    "clear_context",
    "LogContext",
    "log_execution_time",
    # Metrics
    "metrics",
    "MetricsCollector",
    "AuditorMetrics",
    "track_metrics",
    # Retry
    "retry_with_backoff",
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "CircuitState",
    "RetryConfig",
    "CircuitBreakerConfig",
    "get_circuit_breaker",
    "RETRY_CONFIG_OPENAI",
    "RETRY_CONFIG_CHROMADB",
    # Cache
    "EmbeddingCache",
    "InMemoryCache",
    "FileCache",
    "CacheEntry",
    "CacheStats",
    "get_embedding_cache",
    "cached_embedding",
]
