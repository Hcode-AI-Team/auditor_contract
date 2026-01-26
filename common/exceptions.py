"""
Exceções Customizadas
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Define hierarquia de exceções para melhor tratamento de erros.
"""


class AuditorError(Exception):
    """Exceção base para todas as exceções do auditor."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ConfigurationError(AuditorError):
    """Erro de configuração da aplicação."""
    pass


class DocumentLoadError(AuditorError):
    """Erro ao carregar documento (PDF/TXT)."""
    pass


class VectorStoreError(AuditorError):
    """Erro relacionado ao ChromaDB."""
    pass


class AgentError(AuditorError):
    """Erro durante execução do agente."""
    pass


class EmbeddingError(AuditorError):
    """Erro ao gerar embeddings."""
    pass


class LLMError(AuditorError):
    """Erro durante chamada ao LLM."""
    pass


class ValidationError(AuditorError):
    """Erro de validação de dados."""
    pass


class TimeoutError(AuditorError):
    """Erro de timeout em operações."""
    pass


class RateLimitError(AuditorError):
    """Erro de rate limiting."""
    pass
