"""
Testes para AuditorAgent
Auditor de Contratos - Bootcamp Itaú FIAP 2026
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from core.agent import AuditorAgent
from adapters.openai_adapter import OpenAIAdapter
from adapters.chromadb_adapter import ChromaDBAdapter
from domain.contract_schema import ContractMetadata
from common.exceptions import AgentError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_openai_adapter():
    """Cria mock do OpenAI Adapter."""
    adapter = MagicMock(spec=OpenAIAdapter)
    adapter.llm = MagicMock()
    adapter.embeddings = MagicMock()
    adapter._llm_model = "gpt-4o"
    adapter._embedding_model = "text-embedding-3-small"
    return adapter


@pytest.fixture
def mock_chromadb_adapter():
    """Cria mock do ChromaDB Adapter."""
    adapter = MagicMock(spec=ChromaDBAdapter)
    adapter.search = MagicMock(return_value=[])
    adapter.asearch = AsyncMock(return_value=[])
    return adapter


@pytest.fixture
def sample_agent_result():
    """Retorna resultado de exemplo do agente."""
    return {
        "output": """{
            "garantia_tipo": "Alienação Fiduciária",
            "garantia_objeto": "Imóvel Matrícula 12345",
            "taxa_juros": 1.0,
            "prazo_meses": 36,
            "valor_principal": 1500000.0,
            "risco_legal": "Baixo",
            "compliance_check": true
        }""",
        "intermediate_steps": [
            (MagicMock(tool="search_contract"), "resultado 1"),
            (MagicMock(tool="search_contract"), "resultado 2"),
            (MagicMock(tool="extract_clause"), "resultado 3"),
        ]
    }


@pytest.fixture
def sample_invalid_result():
    """Retorna resultado inválido do agente."""
    return {
        "output": "Não encontrei informações suficientes.",
        "intermediate_steps": []
    }


# ============================================================================
# TESTES DE INICIALIZAÇÃO
# ============================================================================

def test_agent_initialization(mock_openai_adapter, mock_chromadb_adapter):
    """Testa inicialização do agente."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter,
                max_iterations=5,
                verbose=False
            )
            
            assert agent._max_iterations == 5
            assert agent._verbose is False
            assert len(agent._tools) > 0


def test_agent_initialization_with_custom_prompt(mock_openai_adapter, mock_chromadb_adapter):
    """Testa inicialização com prompt customizado."""
    custom_prompt = "Custom prompt template {input} {agent_scratchpad} {tools}"
    
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter,
                prompt_template=custom_prompt
            )
            
            assert agent._prompt_template == custom_prompt


def test_agent_properties(mock_openai_adapter, mock_chromadb_adapter):
    """Testa propriedades do agente."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            assert agent.openai_adapter == mock_openai_adapter
            assert agent.chromadb_adapter == mock_chromadb_adapter
            assert isinstance(agent.tools, list)


# ============================================================================
# TESTES DE PARSE
# ============================================================================

def test_parse_result_to_schema_valid(mock_openai_adapter, mock_chromadb_adapter, sample_agent_result):
    """Testa parse de resultado válido."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            metadata = agent.parse_result_to_schema(sample_agent_result)
            
            assert isinstance(metadata, ContractMetadata)
            assert metadata.garantia_tipo == "Alienação Fiduciária"
            assert metadata.taxa_juros == 1.0
            assert metadata.prazo_meses == 36
            assert metadata.valor_principal == 1500000.0
            assert metadata.risco_legal == "Baixo"
            assert metadata.compliance_check is True


def test_parse_result_to_schema_no_json(mock_openai_adapter, mock_chromadb_adapter, sample_invalid_result):
    """Testa parse quando não há JSON no resultado."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            with pytest.raises(AgentError) as exc_info:
                agent.parse_result_to_schema(sample_invalid_result)
            
            assert "JSON" in str(exc_info.value)


def test_parse_result_to_schema_invalid_json(mock_openai_adapter, mock_chromadb_adapter):
    """Testa parse com JSON inválido."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            invalid_result = {
                "output": "{invalid json here",
                "intermediate_steps": []
            }
            
            with pytest.raises(AgentError) as exc_info:
                agent.parse_result_to_schema(invalid_result)
            
            assert "parsear JSON" in str(exc_info.value)


def test_parse_result_to_schema_invalid_schema(mock_openai_adapter, mock_chromadb_adapter):
    """Testa parse com schema inválido (faltando campos)."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            incomplete_result = {
                "output": '{"garantia_tipo": "Test"}',  # Faltam campos obrigatórios
                "intermediate_steps": []
            }
            
            with pytest.raises(AgentError):
                agent.parse_result_to_schema(incomplete_result)


# ============================================================================
# TESTES DE ESTATÍSTICAS
# ============================================================================

def test_get_statistics(mock_openai_adapter, mock_chromadb_adapter, sample_agent_result):
    """Testa extração de estatísticas."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            stats = agent.get_statistics(sample_agent_result)
            
            assert stats["num_iterations"] == 3
            assert stats["num_tool_calls"] == 3
            assert "search_contract" in stats["unique_tools"]
            assert "extract_clause" in stats["unique_tools"]
            assert len(stats["unique_tools"]) == 2


def test_get_statistics_empty(mock_openai_adapter, mock_chromadb_adapter):
    """Testa estatísticas com resultado vazio."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            empty_result = {"output": "", "intermediate_steps": []}
            stats = agent.get_statistics(empty_result)
            
            assert stats["num_iterations"] == 0
            assert stats["num_tool_calls"] == 0
            assert stats["unique_tools"] == []


# ============================================================================
# TESTES DE ANÁLISE (COM MOCKS)
# ============================================================================

def test_analyze_contract_success(mock_openai_adapter, mock_chromadb_adapter, sample_agent_result):
    """Testa análise de contrato com sucesso."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            # Mock do executor
            agent._agent_executor = MagicMock()
            agent._agent_executor.invoke = MagicMock(return_value=sample_agent_result)
            
            result = agent.analyze_contract()
            
            assert "output" in result
            assert "intermediate_steps" in result
            agent._agent_executor.invoke.assert_called_once()


def test_analyze_contract_with_custom_query(mock_openai_adapter, mock_chromadb_adapter, sample_agent_result):
    """Testa análise com query customizada."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            agent._agent_executor = MagicMock()
            agent._agent_executor.invoke = MagicMock(return_value=sample_agent_result)
            
            custom_query = "Busque apenas as garantias do contrato"
            result = agent.analyze_contract(query=custom_query)
            
            # Verifica que a query customizada foi passada
            call_args = agent._agent_executor.invoke.call_args
            assert custom_query in call_args[0][0]["input"]


def test_analyze_contract_error(mock_openai_adapter, mock_chromadb_adapter):
    """Testa tratamento de erro na análise."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            agent._agent_executor = MagicMock()
            agent._agent_executor.invoke = MagicMock(side_effect=Exception("LLM Error"))
            
            with pytest.raises(AgentError) as exc_info:
                agent.analyze_contract()
            
            assert "Erro ao analisar contrato" in str(exc_info.value)


# ============================================================================
# TESTES ASYNC
# ============================================================================

@pytest.mark.asyncio
async def test_aanalyze_contract_success(mock_openai_adapter, mock_chromadb_adapter, sample_agent_result):
    """Testa análise async de contrato com sucesso."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            # Mock do executor async
            agent._agent_executor = MagicMock()
            agent._agent_executor.ainvoke = AsyncMock(return_value=sample_agent_result)
            
            result = await agent.aanalyze_contract()
            
            assert "output" in result
            assert "intermediate_steps" in result
            agent._agent_executor.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_aanalyze_contract_error(mock_openai_adapter, mock_chromadb_adapter):
    """Testa tratamento de erro na análise async."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            agent._agent_executor = MagicMock()
            agent._agent_executor.ainvoke = AsyncMock(side_effect=Exception("Async Error"))
            
            with pytest.raises(AgentError):
                await agent.aanalyze_contract()


@pytest.mark.asyncio
async def test_aanalyze_and_parse(mock_openai_adapter, mock_chromadb_adapter, sample_agent_result):
    """Testa analyze_and_parse async."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            agent._agent_executor = MagicMock()
            agent._agent_executor.ainvoke = AsyncMock(return_value=sample_agent_result)
            
            metadata = await agent.aanalyze_and_parse()
            
            assert isinstance(metadata, ContractMetadata)
            assert metadata.garantia_tipo == "Alienação Fiduciária"


# ============================================================================
# TESTES DE ANALYZE_AND_PARSE
# ============================================================================

def test_analyze_and_parse(mock_openai_adapter, mock_chromadb_adapter, sample_agent_result):
    """Testa analyze_and_parse completo."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            agent._agent_executor = MagicMock()
            agent._agent_executor.invoke = MagicMock(return_value=sample_agent_result)
            
            metadata = agent.analyze_and_parse()
            
            assert isinstance(metadata, ContractMetadata)
            assert metadata.taxa_juros == 1.0


# ============================================================================
# TESTES DE MÉTRICAS
# ============================================================================

def test_get_metrics_summary(mock_openai_adapter, mock_chromadb_adapter):
    """Testa obtenção de resumo de métricas."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            metrics_summary = agent.get_metrics_summary()
            
            assert isinstance(metrics_summary, dict)
            assert "timestamp" in metrics_summary
            assert "counters" in metrics_summary
            assert "gauges" in metrics_summary


# ============================================================================
# TESTES DE DEFAULT QUERY
# ============================================================================

def test_get_default_query(mock_openai_adapter, mock_chromadb_adapter):
    """Testa query padrão."""
    with patch('core.agent.create_contract_tools', return_value=[MagicMock()]):
        with patch('core.agent.create_react_agent', return_value=MagicMock()):
            agent = AuditorAgent(
                openai_adapter=mock_openai_adapter,
                chromadb_adapter=mock_chromadb_adapter
            )
            
            query = agent._get_default_query()
            
            assert "garantia_tipo" in query
            assert "taxa_juros" in query
            assert "prazo_meses" in query
            assert "valor_principal" in query
            assert "risco_legal" in query
            assert "compliance_check" in query
