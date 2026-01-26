"""
API Schemas - Pydantic Models
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Schemas para request/response da API.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class AnalysisStatus(str, Enum):
    """Status de uma análise."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """Níveis de risco."""
    BAIXO = "Baixo"
    MEDIO = "Médio"
    ALTO = "Alto"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class AnalyzeContractRequest(BaseModel):
    """Request para análise de contrato."""
    contract_path: Optional[str] = Field(
        None,
        description="Caminho para o arquivo do contrato"
    )
    contract_text: Optional[str] = Field(
        None,
        description="Texto do contrato (alternativa ao path)"
    )
    custom_query: Optional[str] = Field(
        None,
        description="Query customizada para análise"
    )
    use_hybrid_search: bool = Field(
        True,
        description="Usar busca híbrida (BM25 + semântica)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "contract_path": "v1/contrato_mutuo_exemplo.txt",
                "use_hybrid_search": True
            }
        }


class SearchRequest(BaseModel):
    """Request para busca no contrato."""
    query: str = Field(..., description="Query de busca")
    k: int = Field(5, ge=1, le=20, description="Número de resultados")
    use_hybrid: bool = Field(True, description="Usar busca híbrida")


class IngestRequest(BaseModel):
    """Request para ingestão de documento."""
    file_path: str = Field(..., description="Caminho do arquivo")
    chunk_size: int = Field(500, ge=100, le=2000, description="Tamanho do chunk")
    chunk_overlap: int = Field(50, ge=0, le=200, description="Sobreposição entre chunks")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ContractMetadataResponse(BaseModel):
    """Metadados extraídos do contrato."""
    garantia_tipo: str
    garantia_objeto: str
    taxa_juros: float
    prazo_meses: int
    valor_principal: float
    risco_legal: RiskLevel
    compliance_check: bool
    observacoes: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    """Resultado completo da análise."""
    id: str = Field(..., description="ID único da análise")
    status: AnalysisStatus
    metadata: Optional[ContractMetadataResponse] = None
    raw_output: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class SearchResultItem(BaseModel):
    """Item de resultado de busca."""
    content: str
    score: float
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    rank: int


class SearchResponse(BaseModel):
    """Response de busca."""
    query: str
    results: List[SearchResultItem]
    total_results: int
    search_type: str


class IngestResponse(BaseModel):
    """Response de ingestão."""
    file_path: str
    num_chunks: int
    chunk_size: int
    chunk_overlap: int
    success: bool
    message: str


class HealthResponse(BaseModel):
    """Response de health check."""
    status: str
    version: str
    components: Dict[str, bool]
    timestamp: datetime


class MetricsResponse(BaseModel):
    """Response de métricas."""
    timestamp: datetime
    counters: Dict[str, Any]
    gauges: Dict[str, Any]
    histograms: Dict[str, Any]
    timers: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Response de erro."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
