"""
Testes para OpenAI Adapter
Auditor de Contratos - Bootcamp Itaú FIAP 2026
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from adapters.openai_adapter import OpenAIAdapter
from common.exceptions import ConfigurationError, EmbeddingError, LLMError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def valid_api_key():
    """Retorna API key válida para testes."""
    return "sk-test-key-12345"


@pytest.fixture
def mock_embeddings():
    """Cria mock para embeddings."""
    mock = MagicMock()
    mock.embed_query = MagicMock(return_value=[0.1, 0.2, 0.3] * 512)
    mock.embed_documents = MagicMock(return_value=[[0.1, 0.2, 0.3] * 512])
    mock.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3] * 512)
    mock.aembed_documents = AsyncMock(return_value=[[0.1, 0.2, 0.3] * 512])
    return mock


@pytest.fixture
def mock_llm():
    """Cria mock para LLM."""
    mock = MagicMock()
    mock.invoke = MagicMock(return_value=MagicMock(content="Response"))
    mock.ainvoke = AsyncMock(return_value=MagicMock(content="Async Response"))
    return mock


# ============================================================================
# TESTES DE INICIALIZAÇÃO
# ============================================================================

def test_adapter_initialization_valid_key(valid_api_key):
    """Testa inicialização com API key válida."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    
    assert adapter.api_key == valid_api_key
    assert adapter.llm_model == "gpt-4o"
    assert adapter.embedding_model == "text-embedding-3-small"
    assert adapter.temperature == 0


def test_adapter_initialization_custom_params(valid_api_key):
    """Testa inicialização com parâmetros customizados."""
    adapter = OpenAIAdapter(
        api_key=valid_api_key,
        llm_model="gpt-3.5-turbo",
        embedding_model="text-embedding-ada-002",
        temperature=0.5,
        streaming=False,
        timeout=120
    )
    
    assert adapter._llm_model == "gpt-3.5-turbo"
    assert adapter._embedding_model == "text-embedding-ada-002"
    assert adapter._temperature == 0.5
    assert adapter._streaming is False
    assert adapter._timeout == 120


def test_adapter_initialization_invalid_key_none():
    """Testa que erro é levantado com API key None."""
    with pytest.raises(ConfigurationError):
        OpenAIAdapter(api_key=None)


def test_adapter_initialization_invalid_key_empty():
    """Testa que erro é levantado com API key vazia."""
    with pytest.raises(ConfigurationError):
        OpenAIAdapter(api_key="")


def test_adapter_initialization_invalid_key_format():
    """Testa que erro é levantado com API key em formato inválido."""
    with pytest.raises(ConfigurationError):
        OpenAIAdapter(api_key="invalid-key-without-sk")


# ============================================================================
# TESTES DE LAZY LOADING
# ============================================================================

def test_llm_lazy_loading(valid_api_key):
    """Testa que LLM é criado apenas quando acessado."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    
    # Antes de acessar, deve ser None
    assert adapter._llm is None
    
    # Acessar a propriedade deve criar a instância
    with patch('adapters.openai_adapter.ChatOpenAI') as mock_chat:
        mock_chat.return_value = MagicMock()
        _ = adapter.llm
        mock_chat.assert_called_once()


def test_embeddings_lazy_loading(valid_api_key):
    """Testa que embeddings é criado apenas quando acessado."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    
    # Antes de acessar, deve ser None
    assert adapter._embeddings is None
    
    # Acessar a propriedade deve criar a instância
    with patch('adapters.openai_adapter.OpenAIEmbeddings') as mock_emb:
        mock_emb.return_value = MagicMock()
        _ = adapter.embeddings
        mock_emb.assert_called_once()


def test_llm_singleton(valid_api_key):
    """Testa que LLM retorna mesma instância em múltiplos acessos."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    
    with patch('adapters.openai_adapter.ChatOpenAI') as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        
        llm1 = adapter.llm
        llm2 = adapter.llm
        
        assert llm1 is llm2
        mock_chat.assert_called_once()


# ============================================================================
# TESTES DE EMBED_TEXT (SYNC)
# ============================================================================

def test_embed_text_success(valid_api_key, mock_embeddings):
    """Testa geração de embedding com sucesso."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    adapter._embeddings = mock_embeddings
    
    result = adapter.embed_text("Test text")
    
    assert isinstance(result, list)
    assert len(result) > 0
    mock_embeddings.embed_query.assert_called_once_with("Test text")


def test_embed_text_error(valid_api_key, mock_embeddings):
    """Testa tratamento de erro em embed_text."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    mock_embeddings.embed_query.side_effect = Exception("API Error")
    adapter._embeddings = mock_embeddings
    
    with pytest.raises(EmbeddingError) as exc_info:
        adapter.embed_text("Test text")
    
    assert "Erro ao gerar embedding" in str(exc_info.value)


# ============================================================================
# TESTES DE EMBED_DOCUMENTS (SYNC)
# ============================================================================

def test_embed_documents_success(valid_api_key, mock_embeddings):
    """Testa geração de embeddings múltiplos com sucesso."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    adapter._embeddings = mock_embeddings
    
    texts = ["Text 1", "Text 2", "Text 3"]
    result = adapter.embed_documents(texts)
    
    assert isinstance(result, list)
    mock_embeddings.embed_documents.assert_called_once_with(texts)


def test_embed_documents_error(valid_api_key, mock_embeddings):
    """Testa tratamento de erro em embed_documents."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    mock_embeddings.embed_documents.side_effect = Exception("API Error")
    adapter._embeddings = mock_embeddings
    
    with pytest.raises(EmbeddingError) as exc_info:
        adapter.embed_documents(["Text 1"])
    
    assert "Erro ao gerar embeddings" in str(exc_info.value)


# ============================================================================
# TESTES DE INVOKE (SYNC)
# ============================================================================

def test_invoke_success(valid_api_key, mock_llm):
    """Testa invocação do LLM com sucesso."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    adapter._llm = mock_llm
    
    messages = [MagicMock(content="Hello")]
    result = adapter.invoke(messages)
    
    assert result is not None
    mock_llm.invoke.assert_called_once_with(messages)


def test_invoke_error(valid_api_key, mock_llm):
    """Testa tratamento de erro em invoke."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    mock_llm.invoke.side_effect = Exception("LLM Error")
    adapter._llm = mock_llm
    
    with pytest.raises(LLMError) as exc_info:
        adapter.invoke([MagicMock(content="Hello")])
    
    assert "Erro ao invocar LLM" in str(exc_info.value)


# ============================================================================
# TESTES ASYNC - EMBED_TEXT
# ============================================================================

@pytest.mark.asyncio
async def test_aembed_text_success(valid_api_key, mock_embeddings):
    """Testa geração de embedding async com sucesso."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    adapter._embeddings = mock_embeddings
    
    result = await adapter.aembed_text("Test text")
    
    assert isinstance(result, list)
    mock_embeddings.aembed_query.assert_called_once_with("Test text")


@pytest.mark.asyncio
async def test_aembed_text_error(valid_api_key, mock_embeddings):
    """Testa tratamento de erro em aembed_text."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    mock_embeddings.aembed_query = AsyncMock(side_effect=Exception("Async Error"))
    adapter._embeddings = mock_embeddings
    
    with pytest.raises(EmbeddingError):
        await adapter.aembed_text("Test text")


# ============================================================================
# TESTES ASYNC - EMBED_DOCUMENTS
# ============================================================================

@pytest.mark.asyncio
async def test_aembed_documents_success(valid_api_key, mock_embeddings):
    """Testa geração de embeddings múltiplos async com sucesso."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    adapter._embeddings = mock_embeddings
    
    texts = ["Text 1", "Text 2"]
    result = await adapter.aembed_documents(texts)
    
    assert isinstance(result, list)
    mock_embeddings.aembed_documents.assert_called_once_with(texts)


@pytest.mark.asyncio
async def test_aembed_documents_error(valid_api_key, mock_embeddings):
    """Testa tratamento de erro em aembed_documents."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    mock_embeddings.aembed_documents = AsyncMock(side_effect=Exception("Async Error"))
    adapter._embeddings = mock_embeddings
    
    with pytest.raises(EmbeddingError):
        await adapter.aembed_documents(["Text 1"])


# ============================================================================
# TESTES ASYNC - INVOKE
# ============================================================================

@pytest.mark.asyncio
async def test_ainvoke_success(valid_api_key, mock_llm):
    """Testa invocação async do LLM com sucesso."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    adapter._llm = mock_llm
    
    messages = [MagicMock(content="Hello")]
    result = await adapter.ainvoke(messages)
    
    assert result is not None
    mock_llm.ainvoke.assert_called_once_with(messages)


@pytest.mark.asyncio
async def test_ainvoke_error(valid_api_key, mock_llm):
    """Testa tratamento de erro em ainvoke."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    mock_llm.ainvoke = AsyncMock(side_effect=Exception("Async LLM Error"))
    adapter._llm = mock_llm
    
    with pytest.raises(LLMError):
        await adapter.ainvoke([MagicMock(content="Hello")])


# ============================================================================
# TESTES DE HEALTH CHECK
# ============================================================================

def test_health_check_success(valid_api_key, mock_embeddings):
    """Testa health check com sucesso."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    adapter._embeddings = mock_embeddings
    
    result = adapter.health_check()
    
    assert result is True


def test_health_check_failure(valid_api_key, mock_embeddings):
    """Testa health check com falha."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    mock_embeddings.embed_query.side_effect = Exception("Connection Error")
    adapter._embeddings = mock_embeddings
    
    result = adapter.health_check()
    
    assert result is False


@pytest.mark.asyncio
async def test_ahealth_check_success(valid_api_key, mock_embeddings):
    """Testa health check async com sucesso."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    adapter._embeddings = mock_embeddings
    
    result = await adapter.ahealth_check()
    
    assert result is True


@pytest.mark.asyncio
async def test_ahealth_check_failure(valid_api_key, mock_embeddings):
    """Testa health check async com falha."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    mock_embeddings.aembed_query = AsyncMock(side_effect=Exception("Connection Error"))
    adapter._embeddings = mock_embeddings
    
    result = await adapter.ahealth_check()
    
    assert result is False


# ============================================================================
# TESTES DE PROPERTIES
# ============================================================================

def test_properties_readonly(valid_api_key):
    """Testa que propriedades são somente leitura."""
    adapter = OpenAIAdapter(api_key=valid_api_key)
    
    # Verifica que propriedades retornam valores corretos
    assert adapter.api_key == valid_api_key
    assert adapter.llm_model == "gpt-4o"
    assert adapter.embedding_model == "text-embedding-3-small"
    assert adapter.temperature == 0
