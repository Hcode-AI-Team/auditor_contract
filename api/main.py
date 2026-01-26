"""
FastAPI Application
Auditor de Contratos - Bootcamp Itaú FIAP 2026

API REST para auditoria de contratos com suporte a métricas Prometheus.
"""

import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse

from api.schemas import (
    AnalyzeContractRequest,
    AnalysisResultResponse,
    AnalysisStatus,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    IngestRequest,
    IngestResponse,
    HealthResponse,
    MetricsResponse,
    ErrorResponse,
    ContractMetadataResponse
)

from core.config import Config
from core.agent import AuditorAgent
from adapters.openai_adapter import OpenAIAdapter
from adapters.chromadb_adapter import ChromaDBAdapter
from adapters.document_loader import DocumentLoader
from adapters.hybrid_search import HybridSearchAdapter
from common.logging import get_logger, setup_logging, set_context, LogContext
from common.metrics import metrics, AuditorMetrics
from common.cache import get_embedding_cache
from common.exceptions import AuditorError

logger = get_logger(__name__)

# ============================================================================
# GLOBAL STATE
# ============================================================================

class AppState:
    """Estado global da aplicação."""
    config: Optional[Config] = None
    openai_adapter: Optional[OpenAIAdapter] = None
    chromadb_adapter: Optional[ChromaDBAdapter] = None
    document_loader: Optional[DocumentLoader] = None
    agent: Optional[AuditorAgent] = None
    hybrid_search: Optional[HybridSearchAdapter] = None
    analyses: Dict[str, AnalysisResultResponse] = {}


app_state = AppState()


# ============================================================================
# LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação."""
    # Startup
    logger.info("Starting Auditor API...")
    setup_logging(level="INFO", json_format=False)
    
    try:
        # Carrega configuração
        app_state.config = Config.from_env()
        app_state.config.validate()
        
        # Inicializa adapters
        app_state.openai_adapter = OpenAIAdapter(
            api_key=app_state.config.openai_api_key,
            llm_model=app_state.config.llm_model,
            embedding_model=app_state.config.embedding_model,
            temperature=app_state.config.temperature
        )
        
        app_state.chromadb_adapter = ChromaDBAdapter(
            embeddings=app_state.openai_adapter.embeddings,
            collection_name=app_state.config.collection_name,
            persist_directory=app_state.config.persist_directory
        )
        
        app_state.document_loader = DocumentLoader(
            chunk_size=app_state.config.chunk_size,
            chunk_overlap=app_state.config.chunk_overlap
        )
        
        # Tenta carregar vectorstore existente
        try:
            app_state.chromadb_adapter.load_existing()
            logger.info("Loaded existing vectorstore")
        except Exception:
            logger.info("No existing vectorstore found")
        
        logger.info("Auditor API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Auditor API...")
    metrics.reset()


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Auditor de Contratos API",
    description="""
    API REST para auditoria inteligente de contratos bancários.
    
    ## Funcionalidades
    
    - **Análise de Contratos**: Extrai metadados estruturados usando RAG + Agente ReAct
    - **Busca Híbrida**: Combina BM25 (keyword) com busca semântica
    - **Ingestão de Documentos**: Suporta PDF e TXT
    - **Métricas Prometheus**: Monitoramento de performance
    
    ## Bootcamp Itaú FIAP 2026
    """,
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Middleware para logging e métricas de requests."""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.perf_counter()
    
    # Define contexto de logging
    set_context(LogContext(request_id=request_id))
    
    # Log request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra_data={"request_id": request_id}
    )
    
    # Incrementa contador
    metrics.increment(
        "http_requests_total",
        labels={"method": request.method, "path": request.url.path}
    )
    
    try:
        response = await call_next(request)
        
        duration = time.perf_counter() - start_time
        
        # Log response
        logger.info(
            f"Request completed: {response.status_code}",
            extra_data={
                "request_id": request_id,
                "duration_ms": round(duration * 1000, 2),
                "status_code": response.status_code
            }
        )
        
        # Registra métricas
        metrics.record_time(
            "http_request_duration_seconds",
            duration,
            labels={"method": request.method, "path": request.url.path}
        )
        
        return response
        
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(f"Request failed: {e}", extra_data={"request_id": request_id})
        metrics.increment(
            "http_requests_errors_total",
            labels={"method": request.method, "path": request.url.path}
        )
        raise


# ============================================================================
# HEALTH & METRICS ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check da aplicação.
    
    Verifica status de todos os componentes.
    """
    components = {
        "api": True,
        "openai": False,
        "chromadb": False
    }
    
    # Verifica OpenAI
    if app_state.openai_adapter:
        try:
            components["openai"] = app_state.openai_adapter.health_check()
        except Exception:
            pass
    
    # Verifica ChromaDB
    if app_state.chromadb_adapter:
        try:
            components["chromadb"] = app_state.chromadb_adapter.health_check()
        except Exception:
            pass
    
    status = "healthy" if all(components.values()) else "degraded"
    
    return HealthResponse(
        status=status,
        version="2.0.0",
        components=components,
        timestamp=datetime.utcnow()
    )


@app.get("/metrics", response_class=PlainTextResponse, tags=["Metrics"])
async def prometheus_metrics():
    """
    Métricas no formato Prometheus.
    
    Pode ser scrapeado pelo Prometheus para dashboards Grafana.
    """
    all_metrics = metrics.get_all_metrics()
    
    lines = []
    lines.append("# HELP auditor_metrics Application metrics")
    lines.append("# TYPE auditor_metrics gauge")
    
    # Counters
    for name, values in all_metrics.get("counters", {}).items():
        lines.append(f"# TYPE {name} counter")
        for labels, value in values.items():
            if labels:
                lines.append(f'{name}{{{labels}}} {value}')
            else:
                lines.append(f'{name} {value}')
    
    # Gauges
    for name, values in all_metrics.get("gauges", {}).items():
        lines.append(f"# TYPE {name} gauge")
        for labels, value in values.items():
            if labels:
                lines.append(f'{name}{{{labels}}} {value}')
            else:
                lines.append(f'{name} {value}')
    
    # Timers (como histograms simplificados)
    for name, stats in all_metrics.get("timers", {}).items():
        if stats["count"] > 0:
            lines.append(f"# TYPE {name} summary")
            lines.append(f'{name}_count {stats["count"]}')
            lines.append(f'{name}_sum {stats["sum"]:.6f}')
            lines.append(f'{name}_avg {stats["avg"]:.6f}')
            lines.append(f'{name}_min {stats["min"]:.6f}')
            lines.append(f'{name}_max {stats["max"]:.6f}')
    
    return "\n".join(lines)


@app.get("/metrics/json", response_model=MetricsResponse, tags=["Metrics"])
async def json_metrics():
    """
    Métricas em formato JSON.
    
    Alternativa ao formato Prometheus para debugging.
    """
    all_metrics = metrics.get_all_metrics()
    
    return MetricsResponse(
        timestamp=datetime.utcnow(),
        counters=all_metrics.get("counters", {}),
        gauges=all_metrics.get("gauges", {}),
        histograms=all_metrics.get("histograms", {}),
        timers=all_metrics.get("timers", {})
    )


# ============================================================================
# CONTRACT ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/v1/analyze", response_model=AnalysisResultResponse, tags=["Analysis"])
async def analyze_contract(
    request: AnalyzeContractRequest,
    background_tasks: BackgroundTasks
):
    """
    Analisa um contrato e extrai metadados.
    
    O processo de análise:
    1. Carrega e processa o documento (se path fornecido)
    2. Indexa no vectorstore
    3. Executa agente ReAct para extração
    4. Retorna metadados estruturados
    """
    analysis_id = str(uuid.uuid4())
    
    # Cria registro inicial
    result = AnalysisResultResponse(
        id=analysis_id,
        status=AnalysisStatus.PENDING,
        created_at=datetime.utcnow()
    )
    app_state.analyses[analysis_id] = result
    
    # Verifica se há documento para processar
    if not request.contract_path and not request.contract_text:
        raise HTTPException(
            status_code=400,
            detail="Forneça contract_path ou contract_text"
        )
    
    # Executa análise em background
    background_tasks.add_task(
        _run_analysis,
        analysis_id,
        request
    )
    
    return result


async def _run_analysis(analysis_id: str, request: AnalyzeContractRequest):
    """Executa análise em background."""
    result = app_state.analyses[analysis_id]
    result.status = AnalysisStatus.PROCESSING
    start_time = time.perf_counter()
    
    try:
        # Processa documento se path fornecido
        if request.contract_path:
            if not Path(request.contract_path).exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {request.contract_path}")
            
            chunks = app_state.document_loader.process_document(request.contract_path)
            app_state.chromadb_adapter.create_from_documents(chunks)
            
            # Inicializa hybrid search se solicitado
            if request.use_hybrid_search:
                app_state.hybrid_search = HybridSearchAdapter(
                    chromadb_adapter=app_state.chromadb_adapter
                )
                app_state.hybrid_search.index_documents(chunks)
        
        # Cria agente
        agent = AuditorAgent(
            openai_adapter=app_state.openai_adapter,
            chromadb_adapter=app_state.chromadb_adapter,
            verbose=False
        )
        
        # Executa análise
        agent_result = await agent.aanalyze_contract(request.custom_query)
        
        # Parse resultado
        metadata = agent.parse_result_to_schema(agent_result)
        stats = agent.get_statistics(agent_result)
        
        duration = time.perf_counter() - start_time
        
        # Atualiza resultado
        result.status = AnalysisStatus.COMPLETED
        result.metadata = ContractMetadataResponse(
            garantia_tipo=metadata.garantia_tipo,
            garantia_objeto=metadata.garantia_objeto,
            taxa_juros=metadata.taxa_juros,
            prazo_meses=metadata.prazo_meses,
            valor_principal=metadata.valor_principal,
            risco_legal=metadata.risco_legal,
            compliance_check=metadata.compliance_check,
            observacoes=metadata.observacoes
        )
        result.raw_output = agent_result["output"]
        result.statistics = stats
        result.completed_at = datetime.utcnow()
        result.duration_seconds = round(duration, 2)
        
        # Registra métricas
        AuditorMetrics.record_contract_analyzed(
            success=True,
            risk_level=metadata.risco_legal
        )
        
        logger.info(
            f"Analysis {analysis_id} completed",
            extra_data={"duration": duration, "risk_level": metadata.risco_legal}
        )
        
    except Exception as e:
        result.status = AnalysisStatus.FAILED
        result.error = str(e)
        result.completed_at = datetime.utcnow()
        
        AuditorMetrics.record_contract_analyzed(success=False)
        
        logger.error(f"Analysis {analysis_id} failed: {e}")


@app.get("/api/v1/analyze/{analysis_id}", response_model=AnalysisResultResponse, tags=["Analysis"])
async def get_analysis(analysis_id: str):
    """
    Obtém resultado de uma análise.
    
    Use após chamar /analyze para verificar status e obter resultados.
    """
    if analysis_id not in app_state.analyses:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    
    return app_state.analyses[analysis_id]


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@app.post("/api/v1/search", response_model=SearchResponse, tags=["Search"])
async def search_contract(request: SearchRequest):
    """
    Busca informações no contrato indexado.
    
    Suporta:
    - Busca semântica pura (ChromaDB)
    - Busca híbrida (BM25 + semântica)
    """
    if app_state.chromadb_adapter is None:
        raise HTTPException(
            status_code=400,
            detail="Nenhum contrato indexado. Use /ingest primeiro."
        )
    
    results = []
    search_type = "hybrid" if request.use_hybrid and app_state.hybrid_search else "semantic"
    
    if search_type == "hybrid" and app_state.hybrid_search:
        # Busca híbrida
        hybrid_results = await app_state.hybrid_search.asearch(
            request.query,
            k=request.k
        )
        
        for r in hybrid_results:
            results.append(SearchResultItem(
                content=r.document.page_content,
                score=r.combined_score,
                semantic_score=r.semantic_score,
                keyword_score=r.keyword_score,
                rank=r.rank
            ))
    else:
        # Busca semântica
        docs = await app_state.chromadb_adapter.asearch_with_score(
            request.query,
            k=request.k
        )
        
        for rank, (doc, score) in enumerate(docs, 1):
            results.append(SearchResultItem(
                content=doc.page_content,
                score=1.0 - score,  # Converte distância para similaridade
                rank=rank
            ))
    
    return SearchResponse(
        query=request.query,
        results=results,
        total_results=len(results),
        search_type=search_type
    )


# ============================================================================
# INGESTION ENDPOINTS
# ============================================================================

@app.post("/api/v1/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_document(request: IngestRequest):
    """
    Ingere um documento no sistema.
    
    Processa o documento em chunks e indexa no vectorstore.
    """
    if not Path(request.file_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"Arquivo não encontrado: {request.file_path}"
        )
    
    try:
        # Configura loader com parâmetros do request
        loader = DocumentLoader(
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        
        # Processa documento
        chunks = await loader.aprocess_document(request.file_path)
        
        # Indexa no ChromaDB
        await app_state.chromadb_adapter.acreate_from_documents(chunks)
        
        # Inicializa hybrid search
        app_state.hybrid_search = HybridSearchAdapter(
            chromadb_adapter=app_state.chromadb_adapter
        )
        app_state.hybrid_search.index_documents(chunks)
        
        return IngestResponse(
            file_path=request.file_path,
            num_chunks=len(chunks),
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            success=True,
            message=f"Documento processado: {len(chunks)} chunks indexados"
        )
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CACHE ENDPOINTS
# ============================================================================

@app.get("/api/v1/cache/stats", tags=["Cache"])
async def cache_stats():
    """
    Estatísticas do cache de embeddings.
    """
    cache = get_embedding_cache()
    return cache.get_stats()


@app.delete("/api/v1/cache", tags=["Cache"])
async def clear_cache():
    """
    Limpa o cache de embeddings.
    """
    cache = get_embedding_cache()
    cache.clear()
    return {"message": "Cache limpo com sucesso"}


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(AuditorError)
async def auditor_error_handler(request: Request, exc: AuditorError):
    """Handler para erros do Auditor."""
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.message,
            "detail": str(exc.details) if exc.details else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    """Handler para erros genéricos."""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
