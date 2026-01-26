"""
Testes do módulo de Hybrid Search
Auditor de Contratos - Bootcamp Itaú FIAP 2026
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from langchain.schema import Document

from adapters.hybrid_search import BM25, HybridSearchAdapter, SearchResult


class TestBM25:
    """Testes para BM25."""
    
    @pytest.fixture
    def sample_documents(self):
        """Documentos de exemplo para testes."""
        return [
            Document(page_content="O contrato de mútuo estabelece taxa de juros de 5% ao ano."),
            Document(page_content="A garantia hipotecária incide sobre o imóvel localizado na Rua A."),
            Document(page_content="O prazo do contrato é de 36 meses com parcelas mensais."),
            Document(page_content="As cláusulas penais preveem multa de 2% sobre o valor devido."),
            Document(page_content="O mutuário declara ter recebido o valor de R$ 100.000,00."),
        ]
    
    def test_fit_creates_index(self, sample_documents):
        """Testa que fit cria índice corretamente."""
        bm25 = BM25()
        bm25.fit(sample_documents)
        
        assert bm25.corpus_size == 5
        assert len(bm25.corpus) == 5
        assert len(bm25.doc_freqs) > 0
        assert bm25.avg_doc_length > 0
    
    def test_tokenize_removes_stopwords(self):
        """Testa que tokenização remove stopwords."""
        bm25 = BM25()
        tokens = bm25._tokenize("O contrato de mútuo")
        
        assert "o" not in tokens
        assert "de" not in tokens
        assert "contrato" in tokens
        assert "mútuo" in tokens
    
    def test_tokenize_lowercases(self):
        """Testa que tokenização converte para minúsculas."""
        bm25 = BM25()
        tokens = bm25._tokenize("CONTRATO Garantia HIPOTECA")
        
        assert "contrato" in tokens
        assert "garantia" in tokens
        assert "hipoteca" in tokens
        assert "CONTRATO" not in tokens
    
    def test_search_returns_relevant_results(self, sample_documents):
        """Testa que busca retorna resultados relevantes."""
        bm25 = BM25()
        bm25.fit(sample_documents)
        
        results = bm25.search("taxa de juros", k=3)
        
        assert len(results) <= 3
        assert len(results) > 0
        
        # Primeiro resultado deve ser o documento sobre taxa de juros
        first_idx, first_score = results[0]
        assert first_score > 0
        assert "juros" in sample_documents[first_idx].page_content.lower()
    
    def test_search_empty_query(self, sample_documents):
        """Testa busca com query vazia."""
        bm25 = BM25()
        bm25.fit(sample_documents)
        
        results = bm25.search("")
        
        assert len(results) == 0
    
    def test_search_no_match(self, sample_documents):
        """Testa busca sem match."""
        bm25 = BM25()
        bm25.fit(sample_documents)
        
        results = bm25.search("xyzabc123")  # Termo que não existe
        
        assert len(results) == 0
    
    def test_idf_calculation(self, sample_documents):
        """Testa cálculo de IDF."""
        bm25 = BM25()
        bm25.fit(sample_documents)
        
        # Termos raros devem ter IDF maior
        # "juros" aparece em 1 doc, "contrato" pode aparecer em mais
        if "juros" in bm25.idf and "valor" in bm25.idf:
            # Ambos têm IDF calculado
            assert bm25.idf["juros"] > 0
    
    def test_k1_and_b_parameters(self):
        """Testa parâmetros k1 e b."""
        bm25 = BM25(k1=1.2, b=0.75)
        
        assert bm25.k1 == 1.2
        assert bm25.b == 0.75


class TestHybridSearchAdapter:
    """Testes para HybridSearchAdapter."""
    
    @pytest.fixture
    def mock_chromadb(self):
        """Mock do ChromaDB adapter."""
        mock = MagicMock()
        return mock
    
    @pytest.fixture
    def sample_documents(self):
        """Documentos de exemplo."""
        return [
            Document(page_content="Contrato de mútuo com taxa de juros de 5%."),
            Document(page_content="Garantia hipotecária sobre imóvel."),
            Document(page_content="Prazo de 36 meses."),
        ]
    
    def test_initialization(self, mock_chromadb):
        """Testa inicialização."""
        adapter = HybridSearchAdapter(
            chromadb_adapter=mock_chromadb,
            alpha=0.7,
            rrf_k=60
        )
        
        assert adapter._alpha == 0.7
        assert adapter._rrf_k == 60
    
    def test_index_documents(self, mock_chromadb, sample_documents):
        """Testa indexação de documentos."""
        adapter = HybridSearchAdapter(chromadb_adapter=mock_chromadb)
        adapter.index_documents(sample_documents)
        
        assert len(adapter._documents) == 3
        assert adapter._bm25 is not None
        assert adapter._bm25.corpus_size == 3
    
    def test_search_without_index(self, mock_chromadb):
        """Testa busca sem índice."""
        adapter = HybridSearchAdapter(chromadb_adapter=mock_chromadb)
        
        results = adapter.search("test query")
        
        assert len(results) == 0
    
    def test_search_combines_results(self, mock_chromadb, sample_documents):
        """Testa que busca combina resultados."""
        # Configura mock do ChromaDB
        mock_chromadb.search_with_score.return_value = [
            (sample_documents[0], 0.1),
            (sample_documents[1], 0.3),
        ]
        
        adapter = HybridSearchAdapter(chromadb_adapter=mock_chromadb, alpha=0.5)
        adapter.index_documents(sample_documents)
        
        results = adapter.search("juros", k=2)
        
        # Deve retornar SearchResult
        assert all(isinstance(r, SearchResult) for r in results)
        assert len(results) <= 2
    
    def test_rrf_score_calculation(self, mock_chromadb):
        """Testa cálculo do score RRF."""
        adapter = HybridSearchAdapter(chromadb_adapter=mock_chromadb, rrf_k=60)
        
        # RRF score para rank 1: 1/(60+1) = ~0.0164
        score_rank_1 = adapter._rrf_score(1)
        score_rank_2 = adapter._rrf_score(2)
        
        assert score_rank_1 > score_rank_2
        assert abs(score_rank_1 - 1/61) < 0.001
    
    def test_alpha_weighting(self, mock_chromadb, sample_documents):
        """Testa ponderação por alpha."""
        # Alpha = 1.0 deve dar peso total para semântico
        adapter_semantic = HybridSearchAdapter(chromadb_adapter=mock_chromadb, alpha=1.0)
        
        # Alpha = 0.0 deve dar peso total para keyword
        adapter_keyword = HybridSearchAdapter(chromadb_adapter=mock_chromadb, alpha=0.0)
        
        assert adapter_semantic._alpha == 1.0
        assert adapter_keyword._alpha == 0.0
    
    def test_get_documents(self, mock_chromadb, sample_documents):
        """Testa get_documents."""
        adapter = HybridSearchAdapter(chromadb_adapter=mock_chromadb)
        adapter.index_documents(sample_documents)
        
        docs = adapter.get_documents()
        
        assert len(docs) == 3
        assert docs == sample_documents
    
    @pytest.mark.asyncio
    async def test_async_search(self, mock_chromadb, sample_documents):
        """Testa busca assíncrona."""
        # Configura mock
        mock_chromadb.asearch_with_score = MagicMock(return_value=[
            (sample_documents[0], 0.1),
        ])
        
        adapter = HybridSearchAdapter(chromadb_adapter=mock_chromadb)
        adapter.index_documents(sample_documents)
        
        results = await adapter.asearch("juros", k=2)
        
        assert isinstance(results, list)
    
    def test_normalize_scores(self, mock_chromadb):
        """Testa normalização de scores."""
        adapter = HybridSearchAdapter(chromadb_adapter=mock_chromadb)
        
        # Scores variados
        scores = [0.1, 0.5, 0.9]
        normalized = adapter._normalize_scores(scores)
        
        assert min(normalized) == 0.0
        assert max(normalized) == 1.0
        
        # Scores iguais
        equal_scores = [0.5, 0.5, 0.5]
        normalized_equal = adapter._normalize_scores(equal_scores)
        assert all(s == 1.0 for s in normalized_equal)
        
        # Lista vazia
        assert adapter._normalize_scores([]) == []


class TestSearchResult:
    """Testes para SearchResult."""
    
    def test_dataclass_fields(self):
        """Testa campos do dataclass."""
        doc = Document(page_content="test")
        result = SearchResult(
            document=doc,
            semantic_score=0.8,
            keyword_score=0.6,
            combined_score=0.7,
            rank=1
        )
        
        assert result.document == doc
        assert result.semantic_score == 0.8
        assert result.keyword_score == 0.6
        assert result.combined_score == 0.7
        assert result.rank == 1
    
    def test_default_values(self):
        """Testa valores padrão."""
        doc = Document(page_content="test")
        result = SearchResult(document=doc)
        
        assert result.semantic_score == 0.0
        assert result.keyword_score == 0.0
        assert result.combined_score == 0.0
        assert result.rank == 0
