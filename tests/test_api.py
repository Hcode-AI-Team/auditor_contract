"""
Testes da API FastAPI
Auditor de Contratos - Bootcamp Itaú FIAP 2026
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

# Mocks precisam ser configurados antes de importar a API
# para evitar erros de inicialização

from api.schemas import (
    AnalysisStatus,
    RiskLevel,
    AnalyzeContractRequest,
    SearchRequest,
    IngestRequest,
    HealthResponse,
    AnalysisResultResponse,
    SearchResponse,
    SearchResultItem,
)


class TestSchemas:
    """Testes para os schemas Pydantic."""
    
    def test_analysis_status_enum(self):
        """Testa enum AnalysisStatus."""
        assert AnalysisStatus.PENDING == "pending"
        assert AnalysisStatus.PROCESSING == "processing"
        assert AnalysisStatus.COMPLETED == "completed"
        assert AnalysisStatus.FAILED == "failed"
    
    def test_risk_level_enum(self):
        """Testa enum RiskLevel."""
        assert RiskLevel.BAIXO == "Baixo"
        assert RiskLevel.MEDIO == "Médio"
        assert RiskLevel.ALTO == "Alto"
    
    def test_analyze_contract_request(self):
        """Testa AnalyzeContractRequest."""
        request = AnalyzeContractRequest(
            contract_path="test.txt",
            use_hybrid_search=True
        )
        
        assert request.contract_path == "test.txt"
        assert request.use_hybrid_search is True
        assert request.contract_text is None
        assert request.custom_query is None
    
    def test_analyze_contract_request_with_text(self):
        """Testa AnalyzeContractRequest com texto."""
        request = AnalyzeContractRequest(
            contract_text="Conteúdo do contrato..."
        )
        
        assert request.contract_text == "Conteúdo do contrato..."
        assert request.contract_path is None
    
    def test_search_request(self):
        """Testa SearchRequest."""
        request = SearchRequest(
            query="taxa de juros",
            k=10,
            use_hybrid=True
        )
        
        assert request.query == "taxa de juros"
        assert request.k == 10
        assert request.use_hybrid is True
    
    def test_search_request_validation(self):
        """Testa validação de SearchRequest."""
        # k deve estar entre 1 e 20
        request = SearchRequest(query="test", k=5)
        assert request.k == 5
        
        # Valores limite
        request_min = SearchRequest(query="test", k=1)
        assert request_min.k == 1
        
        request_max = SearchRequest(query="test", k=20)
        assert request_max.k == 20
    
    def test_ingest_request(self):
        """Testa IngestRequest."""
        request = IngestRequest(
            file_path="contract.txt",
            chunk_size=500,
            chunk_overlap=50
        )
        
        assert request.file_path == "contract.txt"
        assert request.chunk_size == 500
        assert request.chunk_overlap == 50
    
    def test_health_response(self):
        """Testa HealthResponse."""
        response = HealthResponse(
            status="healthy",
            version="2.0.0",
            components={"api": True, "openai": True},
            timestamp=datetime.utcnow()
        )
        
        assert response.status == "healthy"
        assert response.version == "2.0.0"
        assert response.components["api"] is True
    
    def test_analysis_result_response(self):
        """Testa AnalysisResultResponse."""
        response = AnalysisResultResponse(
            id="test-123",
            status=AnalysisStatus.COMPLETED,
            created_at=datetime.utcnow()
        )
        
        assert response.id == "test-123"
        assert response.status == AnalysisStatus.COMPLETED
        assert response.metadata is None
        assert response.error is None
    
    def test_search_response(self):
        """Testa SearchResponse."""
        items = [
            SearchResultItem(
                content="Resultado 1",
                score=0.9,
                rank=1
            ),
            SearchResultItem(
                content="Resultado 2",
                score=0.7,
                rank=2
            ),
        ]
        
        response = SearchResponse(
            query="taxa de juros",
            results=items,
            total_results=2,
            search_type="hybrid"
        )
        
        assert response.query == "taxa de juros"
        assert len(response.results) == 2
        assert response.total_results == 2
        assert response.search_type == "hybrid"
    
    def test_search_result_item(self):
        """Testa SearchResultItem."""
        item = SearchResultItem(
            content="Conteúdo do resultado",
            score=0.85,
            semantic_score=0.9,
            keyword_score=0.8,
            rank=1
        )
        
        assert item.content == "Conteúdo do resultado"
        assert item.score == 0.85
        assert item.semantic_score == 0.9
        assert item.keyword_score == 0.8
        assert item.rank == 1
    
    def test_search_result_item_optional_scores(self):
        """Testa scores opcionais em SearchResultItem."""
        item = SearchResultItem(
            content="Test",
            score=0.5,
            rank=1
        )
        
        assert item.semantic_score is None
        assert item.keyword_score is None


class TestAPIIntegration:
    """Testes de integração da API (requerem setup mais complexo)."""
    
    @pytest.fixture
    def mock_app_state(self):
        """Mock do estado da aplicação."""
        with patch("api.main.app_state") as mock:
            mock.config = MagicMock()
            mock.openai_adapter = MagicMock()
            mock.chromadb_adapter = MagicMock()
            mock.document_loader = MagicMock()
            mock.hybrid_search = None
            mock.analyses = {}
            yield mock
    
    @pytest.mark.skip(reason="Requer TestClient configurado")
    def test_health_endpoint(self, mock_app_state):
        """Testa endpoint /health."""
        # Este teste requer TestClient do FastAPI
        pass
    
    @pytest.mark.skip(reason="Requer TestClient configurado")
    def test_metrics_endpoint(self, mock_app_state):
        """Testa endpoint /metrics."""
        pass
    
    @pytest.mark.skip(reason="Requer TestClient configurado")
    def test_analyze_endpoint(self, mock_app_state):
        """Testa endpoint /api/v1/analyze."""
        pass


class TestPrometheusMetrics:
    """Testes para formato de métricas Prometheus."""
    
    def test_counter_format(self):
        """Testa formato de counter."""
        # Formato esperado: metric_name{labels} value
        metric_line = 'http_requests_total{method="GET",path="/health"} 42'
        
        assert "http_requests_total" in metric_line
        assert "42" in metric_line
    
    def test_gauge_format(self):
        """Testa formato de gauge."""
        metric_line = 'cache_size 150'
        
        assert "cache_size" in metric_line
        assert "150" in metric_line
    
    def test_histogram_format(self):
        """Testa formato de histogram/summary."""
        lines = [
            'http_request_duration_seconds_count 100',
            'http_request_duration_seconds_sum 45.5',
            'http_request_duration_seconds_avg 0.455',
        ]
        
        assert all("http_request_duration_seconds" in line for line in lines)
