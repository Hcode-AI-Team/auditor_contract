"""
Testes para ChromaDB Adapter
Auditor de Contratos - Bootcamp Itaú FIAP 2026
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from langchain.schema import Document
from adapters.chromadb_adapter import ChromaDBAdapter
from common.exceptions import VectorStoreError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_embeddings():
    """Cria mock para embeddings."""
    mock = MagicMock()
    mock.embed_query = MagicMock(return_value=[0.1, 0.2, 0.3] * 512)
    mock.embed_documents = MagicMock(return_value=[[0.1, 0.2, 0.3] * 512])
    return mock


@pytest.fixture
def mock_vectorstore():
    """Cria mock para vectorstore."""
    mock = MagicMock()
    mock.similarity_search = MagicMock(return_value=[
        Document(page_content="Test content 1"),
        Document(page_content="Test content 2")
    ])
    mock.similarity_search_with_score = MagicMock(return_value=[
        (Document(page_content="Test content 1"), 0.95),
        (Document(page_content="Test content 2"), 0.85)
    ])
    mock.add_documents = MagicMock()
    mock.delete_collection = MagicMock()
    return mock


@pytest.fixture
def sample_documents():
    """Retorna documentos de exemplo."""
    return [
        Document(page_content="Cláusula 1: Garantias do contrato"),
        Document(page_content="Cláusula 2: Taxa de juros"),
        Document(page_content="Cláusula 3: Prazo de pagamento")
    ]


# ============================================================================
# TESTES DE INICIALIZAÇÃO
# ============================================================================

def test_adapter_initialization(mock_embeddings):
    """Testa inicialização do adapter."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    
    assert adapter.embeddings == mock_embeddings
    assert adapter.collection_name == "contratos"
    assert adapter.persist_directory == "./chroma_db"
    assert adapter._vectorstore is None


def test_adapter_initialization_custom_params(mock_embeddings):
    """Testa inicialização com parâmetros customizados."""
    adapter = ChromaDBAdapter(
        embeddings=mock_embeddings,
        collection_name="custom_collection",
        persist_directory="./custom_db"
    )
    
    assert adapter.collection_name == "custom_collection"
    assert adapter.persist_directory == "./custom_db"


# ============================================================================
# TESTES DE PROPERTIES
# ============================================================================

def test_vectorstore_property_not_initialized(mock_embeddings):
    """Testa que erro é levantado quando vectorstore não foi inicializado."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    
    with pytest.raises(VectorStoreError) as exc_info:
        _ = adapter.vectorstore
    
    assert "não inicializado" in str(exc_info.value)


def test_vectorstore_property_initialized(mock_embeddings, mock_vectorstore):
    """Testa acesso ao vectorstore quando inicializado."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    adapter._vectorstore = mock_vectorstore
    
    result = adapter.vectorstore
    
    assert result == mock_vectorstore


# ============================================================================
# TESTES DE CREATE_FROM_DOCUMENTS
# ============================================================================

def test_create_from_documents_success(mock_embeddings, sample_documents):
    """Testa criação de vectorstore a partir de documentos."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    
    with patch('adapters.chromadb_adapter.Chroma') as mock_chroma:
        mock_chroma.from_documents = MagicMock(return_value=MagicMock())
        
        adapter.create_from_documents(sample_documents)
        
        mock_chroma.from_documents.assert_called_once()
        assert adapter._vectorstore is not None


def test_create_from_documents_error(mock_embeddings, sample_documents):
    """Testa tratamento de erro ao criar vectorstore."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    
    with patch('adapters.chromadb_adapter.Chroma') as mock_chroma:
        mock_chroma.from_documents.side_effect = Exception("DB Error")
        
        with pytest.raises(VectorStoreError) as exc_info:
            adapter.create_from_documents(sample_documents)
        
        assert "Erro ao criar vectorstore" in str(exc_info.value)


# ============================================================================
# TESTES DE LOAD_EXISTING
# ============================================================================

def test_load_existing_success(mock_embeddings):
    """Testa carregamento de vectorstore existente."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    
    with patch('adapters.chromadb_adapter.Chroma') as mock_chroma:
        mock_instance = MagicMock()
        mock_chroma.return_value = mock_instance
        
        adapter.load_existing()
        
        mock_chroma.assert_called_once()
        assert adapter._vectorstore == mock_instance


def test_load_existing_error(mock_embeddings):
    """Testa tratamento de erro ao carregar vectorstore."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    
    with patch('adapters.chromadb_adapter.Chroma') as mock_chroma:
        mock_chroma.side_effect = Exception("Load Error")
        
        with pytest.raises(VectorStoreError) as exc_info:
            adapter.load_existing()
        
        assert "Erro ao carregar vectorstore" in str(exc_info.value)


# ============================================================================
# TESTES DE SEARCH
# ============================================================================

def test_search_success(mock_embeddings, mock_vectorstore):
    """Testa busca por similaridade com sucesso."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    adapter._vectorstore = mock_vectorstore
    
    results = adapter.search("garantias", k=3)
    
    assert len(results) == 2
    assert isinstance(results[0], Document)
    mock_vectorstore.similarity_search.assert_called_once_with("garantias", k=3)


def test_search_custom_k(mock_embeddings, mock_vectorstore):
    """Testa busca com k customizado."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    adapter._vectorstore = mock_vectorstore
    
    adapter.search("juros", k=5)
    
    mock_vectorstore.similarity_search.assert_called_once_with("juros", k=5)


def test_search_error(mock_embeddings, mock_vectorstore):
    """Testa tratamento de erro na busca."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    mock_vectorstore.similarity_search.side_effect = Exception("Search Error")
    adapter._vectorstore = mock_vectorstore
    
    with pytest.raises(VectorStoreError) as exc_info:
        adapter.search("test")
    
    assert "Erro ao buscar" in str(exc_info.value)


# ============================================================================
# TESTES DE SEARCH_WITH_SCORE
# ============================================================================

def test_search_with_score_success(mock_embeddings, mock_vectorstore):
    """Testa busca com score com sucesso."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    adapter._vectorstore = mock_vectorstore
    
    results = adapter.search_with_score("garantias", k=3)
    
    assert len(results) == 2
    assert isinstance(results[0], tuple)
    assert isinstance(results[0][0], Document)
    assert isinstance(results[0][1], float)
    mock_vectorstore.similarity_search_with_score.assert_called_once()


def test_search_with_score_error(mock_embeddings, mock_vectorstore):
    """Testa tratamento de erro na busca com score."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    mock_vectorstore.similarity_search_with_score.side_effect = Exception("Score Error")
    adapter._vectorstore = mock_vectorstore
    
    with pytest.raises(VectorStoreError):
        adapter.search_with_score("test")


# ============================================================================
# TESTES DE ADD_DOCUMENTS
# ============================================================================

def test_add_documents_success(mock_embeddings, mock_vectorstore, sample_documents):
    """Testa adição de documentos com sucesso."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    adapter._vectorstore = mock_vectorstore
    
    adapter.add_documents(sample_documents)
    
    mock_vectorstore.add_documents.assert_called_once_with(sample_documents)


def test_add_documents_error(mock_embeddings, mock_vectorstore, sample_documents):
    """Testa tratamento de erro ao adicionar documentos."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    mock_vectorstore.add_documents.side_effect = Exception("Add Error")
    adapter._vectorstore = mock_vectorstore
    
    with pytest.raises(VectorStoreError) as exc_info:
        adapter.add_documents(sample_documents)
    
    assert "Erro ao adicionar documentos" in str(exc_info.value)


# ============================================================================
# TESTES DE DELETE_COLLECTION
# ============================================================================

def test_delete_collection_success(mock_embeddings, mock_vectorstore):
    """Testa deleção de coleção com sucesso."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    adapter._vectorstore = mock_vectorstore
    
    adapter.delete_collection()
    
    mock_vectorstore.delete_collection.assert_called_once()
    assert adapter._vectorstore is None


def test_delete_collection_when_none(mock_embeddings):
    """Testa deleção quando vectorstore é None."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    
    # Não deve levantar erro
    adapter.delete_collection()


def test_delete_collection_error(mock_embeddings, mock_vectorstore):
    """Testa tratamento de erro ao deletar coleção."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    mock_vectorstore.delete_collection.side_effect = Exception("Delete Error")
    adapter._vectorstore = mock_vectorstore
    
    with pytest.raises(VectorStoreError):
        adapter.delete_collection()


# ============================================================================
# TESTES ASYNC
# ============================================================================

@pytest.mark.asyncio
async def test_acreate_from_documents(mock_embeddings, sample_documents):
    """Testa criação async de vectorstore."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    
    with patch('adapters.chromadb_adapter.Chroma') as mock_chroma:
        mock_chroma.from_documents = MagicMock(return_value=MagicMock())
        
        await adapter.acreate_from_documents(sample_documents)
        
        assert adapter._vectorstore is not None


@pytest.mark.asyncio
async def test_aload_existing(mock_embeddings):
    """Testa carregamento async de vectorstore existente."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    
    with patch('adapters.chromadb_adapter.Chroma') as mock_chroma:
        mock_chroma.return_value = MagicMock()
        
        await adapter.aload_existing()
        
        assert adapter._vectorstore is not None


@pytest.mark.asyncio
async def test_asearch(mock_embeddings, mock_vectorstore):
    """Testa busca async por similaridade."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    adapter._vectorstore = mock_vectorstore
    
    results = await adapter.asearch("garantias", k=3)
    
    assert len(results) == 2


@pytest.mark.asyncio
async def test_asearch_with_score(mock_embeddings, mock_vectorstore):
    """Testa busca async com score."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    adapter._vectorstore = mock_vectorstore
    
    results = await adapter.asearch_with_score("garantias", k=3)
    
    assert len(results) == 2
    assert isinstance(results[0], tuple)


@pytest.mark.asyncio
async def test_aadd_documents(mock_embeddings, mock_vectorstore, sample_documents):
    """Testa adição async de documentos."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    adapter._vectorstore = mock_vectorstore
    
    await adapter.aadd_documents(sample_documents)
    
    mock_vectorstore.add_documents.assert_called_once()


# ============================================================================
# TESTES DE HEALTH CHECK
# ============================================================================

def test_health_check_success(mock_embeddings, mock_vectorstore):
    """Testa health check com sucesso."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    adapter._vectorstore = mock_vectorstore
    
    result = adapter.health_check()
    
    assert result is True


def test_health_check_not_initialized(mock_embeddings):
    """Testa health check quando vectorstore não foi inicializado."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    
    result = adapter.health_check()
    
    assert result is False


def test_health_check_search_error(mock_embeddings, mock_vectorstore):
    """Testa health check quando busca falha."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    mock_vectorstore.similarity_search.side_effect = Exception("Search Error")
    adapter._vectorstore = mock_vectorstore
    
    result = adapter.health_check()
    
    assert result is False


@pytest.mark.asyncio
async def test_ahealth_check_success(mock_embeddings, mock_vectorstore):
    """Testa health check async com sucesso."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    adapter._vectorstore = mock_vectorstore
    
    result = await adapter.ahealth_check()
    
    assert result is True


@pytest.mark.asyncio
async def test_ahealth_check_not_initialized(mock_embeddings):
    """Testa health check async quando vectorstore não foi inicializado."""
    adapter = ChromaDBAdapter(embeddings=mock_embeddings)
    
    result = await adapter.ahealth_check()
    
    assert result is False
