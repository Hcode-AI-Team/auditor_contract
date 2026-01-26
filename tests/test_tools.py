"""
Testes para Tools
Auditor de Contratos - Bootcamp Itaú FIAP 2026
"""

import pytest
from unittest.mock import MagicMock
from langchain.schema import Document
from langchain.tools import Tool
from domain.tools import create_contract_tools, create_financial_calculator_tool


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_vectorstore_adapter():
    """Cria mock do vectorstore adapter."""
    adapter = MagicMock()
    adapter.search = MagicMock(return_value=[
        Document(page_content="Cláusula 1: A garantia será..."),
        Document(page_content="Cláusula 2: Os juros serão de 1% ao mês."),
        Document(page_content="Cláusula 3: O prazo é de 36 meses.")
    ])
    return adapter


@pytest.fixture
def mock_vectorstore_adapter_empty():
    """Cria mock do vectorstore adapter que retorna vazio."""
    adapter = MagicMock()
    adapter.search = MagicMock(return_value=[])
    return adapter


@pytest.fixture
def mock_vectorstore_adapter_error():
    """Cria mock do vectorstore adapter que gera erro."""
    adapter = MagicMock()
    adapter.search = MagicMock(side_effect=Exception("Search Error"))
    return adapter


# ============================================================================
# TESTES DE CREATE_CONTRACT_TOOLS
# ============================================================================

def test_create_contract_tools_returns_list(mock_vectorstore_adapter):
    """Testa que create_contract_tools retorna lista de tools."""
    tools = create_contract_tools(mock_vectorstore_adapter)
    
    assert isinstance(tools, list)
    assert len(tools) == 2
    assert all(isinstance(tool, Tool) for tool in tools)


def test_create_contract_tools_has_search_contract(mock_vectorstore_adapter):
    """Testa que search_contract está nas tools."""
    tools = create_contract_tools(mock_vectorstore_adapter)
    
    tool_names = [tool.name for tool in tools]
    assert "search_contract" in tool_names


def test_create_contract_tools_has_extract_clause(mock_vectorstore_adapter):
    """Testa que extract_clause está nas tools."""
    tools = create_contract_tools(mock_vectorstore_adapter)
    
    tool_names = [tool.name for tool in tools]
    assert "extract_clause" in tool_names


def test_tools_have_descriptions(mock_vectorstore_adapter):
    """Testa que todas as tools têm descrições."""
    tools = create_contract_tools(mock_vectorstore_adapter)
    
    for tool in tools:
        assert tool.description is not None
        assert len(tool.description) > 0


# ============================================================================
# TESTES DE SEARCH_CONTRACT TOOL
# ============================================================================

def test_search_contract_success(mock_vectorstore_adapter):
    """Testa busca no contrato com sucesso."""
    tools = create_contract_tools(mock_vectorstore_adapter)
    search_tool = next(t for t in tools if t.name == "search_contract")
    
    result = search_tool.func("garantias")
    
    assert "Chunks encontrados" in result
    assert "Chunk 1:" in result
    mock_vectorstore_adapter.search.assert_called_once_with("garantias", k=3)


def test_search_contract_empty_results(mock_vectorstore_adapter_empty):
    """Testa busca que não encontra resultados."""
    tools = create_contract_tools(mock_vectorstore_adapter_empty)
    search_tool = next(t for t in tools if t.name == "search_contract")
    
    result = search_tool.func("termo inexistente")
    
    assert "Nenhum chunk relevante" in result


def test_search_contract_error_handling(mock_vectorstore_adapter_error):
    """Testa tratamento de erro na busca."""
    tools = create_contract_tools(mock_vectorstore_adapter_error)
    search_tool = next(t for t in tools if t.name == "search_contract")
    
    result = search_tool.func("test")
    
    assert "Erro ao buscar" in result


def test_search_contract_different_queries(mock_vectorstore_adapter):
    """Testa busca com diferentes queries."""
    tools = create_contract_tools(mock_vectorstore_adapter)
    search_tool = next(t for t in tools if t.name == "search_contract")
    
    queries = ["juros", "prazo", "valor", "garantias"]
    
    for query in queries:
        result = search_tool.func(query)
        assert "Chunks encontrados" in result or "Nenhum chunk" in result


# ============================================================================
# TESTES DE EXTRACT_CLAUSE TOOL
# ============================================================================

def test_extract_clause_success(mock_vectorstore_adapter):
    """Testa extração de cláusula com sucesso."""
    tools = create_contract_tools(mock_vectorstore_adapter)
    extract_tool = next(t for t in tools if t.name == "extract_clause")
    
    result = extract_tool.func("1")
    
    assert "Cláusula 1:" in result
    mock_vectorstore_adapter.search.assert_called()


def test_extract_clause_not_found(mock_vectorstore_adapter_empty):
    """Testa extração de cláusula não encontrada."""
    tools = create_contract_tools(mock_vectorstore_adapter_empty)
    extract_tool = next(t for t in tools if t.name == "extract_clause")
    
    result = extract_tool.func("99")
    
    assert "não encontrada" in result


def test_extract_clause_error_handling(mock_vectorstore_adapter_error):
    """Testa tratamento de erro na extração."""
    tools = create_contract_tools(mock_vectorstore_adapter_error)
    extract_tool = next(t for t in tools if t.name == "extract_clause")
    
    result = extract_tool.func("1")
    
    assert "Erro ao extrair" in result


def test_extract_clause_different_formats(mock_vectorstore_adapter):
    """Testa extração com diferentes formatos de número."""
    tools = create_contract_tools(mock_vectorstore_adapter)
    extract_tool = next(t for t in tools if t.name == "extract_clause")
    
    formats = ["1", "5.1", "QUARTA", "primeira"]
    
    for format_num in formats:
        result = extract_tool.func(format_num)
        # Deve retornar resultado ou mensagem de não encontrado
        assert "Cláusula" in result or "não encontrada" in result


def test_extract_clause_uppercase_conversion(mock_vectorstore_adapter):
    """Testa que número da cláusula é convertido para maiúsculas."""
    mock_adapter = MagicMock()
    mock_adapter.search = MagicMock(return_value=[
        Document(page_content="CLÁUSULA QUINTA: Conteúdo...")
    ])
    
    tools = create_contract_tools(mock_adapter)
    extract_tool = next(t for t in tools if t.name == "extract_clause")
    
    extract_tool.func("quinta")
    
    # Verifica que a busca foi feita com maiúsculas
    call_args = mock_adapter.search.call_args
    assert "QUINTA" in call_args[0][0]


# ============================================================================
# TESTES DE FINANCIAL CALCULATOR TOOL
# ============================================================================

def test_create_financial_calculator_tool():
    """Testa criação da tool de cálculo financeiro."""
    tool = create_financial_calculator_tool()
    
    assert isinstance(tool, Tool)
    assert tool.name == "calculate_interest"
    assert tool.description is not None


def test_financial_calculator_success():
    """Testa cálculo de juros compostos com sucesso."""
    tool = create_financial_calculator_tool()
    
    result = tool.func("1500000,1.0,36")
    
    assert "Principal" in result
    assert "Taxa" in result
    assert "Prazo" in result
    assert "Montante Final" in result
    assert "Juros Totais" in result


def test_financial_calculator_different_values():
    """Testa cálculo com diferentes valores."""
    tool = create_financial_calculator_tool()
    
    test_cases = [
        ("100000,0.5,12", True),  # 100k, 0.5% ao mês, 12 meses
        ("500000,1.5,24", True),  # 500k, 1.5% ao mês, 24 meses
        ("1000000,2.0,60", True), # 1M, 2% ao mês, 60 meses
    ]
    
    for params, should_work in test_cases:
        result = tool.func(params)
        if should_work:
            assert "Montante Final" in result
            assert "Erro" not in result


def test_financial_calculator_invalid_format():
    """Testa cálculo com formato inválido."""
    tool = create_financial_calculator_tool()
    
    result = tool.func("invalid_format")
    
    assert "Erro no cálculo" in result


def test_financial_calculator_missing_params():
    """Testa cálculo com parâmetros faltando."""
    tool = create_financial_calculator_tool()
    
    result = tool.func("1500000,1.0")  # Falta o prazo
    
    assert "Erro" in result


def test_financial_calculator_non_numeric():
    """Testa cálculo com valores não numéricos."""
    tool = create_financial_calculator_tool()
    
    result = tool.func("abc,def,ghi")
    
    assert "Erro" in result


def test_financial_calculator_calculation_accuracy():
    """Testa precisão do cálculo de juros compostos."""
    tool = create_financial_calculator_tool()
    
    # 100000 com 1% ao mês por 12 meses
    # M = 100000 * (1.01)^12 = 112682.50...
    result = tool.func("100000,1.0,12")
    
    assert "112,682" in result or "112.682" in result  # Aproximadamente


# ============================================================================
# TESTES DE INTEGRAÇÃO
# ============================================================================

def test_tools_can_be_called_sequentially(mock_vectorstore_adapter):
    """Testa que tools podem ser chamadas em sequência."""
    tools = create_contract_tools(mock_vectorstore_adapter)
    search_tool = next(t for t in tools if t.name == "search_contract")
    extract_tool = next(t for t in tools if t.name == "extract_clause")
    
    # Simula sequência de chamadas como um agente faria
    result1 = search_tool.func("garantias")
    result2 = extract_tool.func("1")
    result3 = search_tool.func("juros")
    
    assert "Chunks encontrados" in result1
    assert "Cláusula" in result2
    assert "Chunks encontrados" in result3


def test_all_tools_have_required_attributes(mock_vectorstore_adapter):
    """Testa que todas as tools têm atributos necessários."""
    tools = create_contract_tools(mock_vectorstore_adapter)
    
    for tool in tools:
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'func')
        assert hasattr(tool, 'description')
        assert callable(tool.func)


def test_tool_descriptions_are_helpful(mock_vectorstore_adapter):
    """Testa que descrições das tools são úteis para o LLM."""
    tools = create_contract_tools(mock_vectorstore_adapter)
    
    search_tool = next(t for t in tools if t.name == "search_contract")
    extract_tool = next(t for t in tools if t.name == "extract_clause")
    
    # Descrições devem incluir exemplos de uso
    assert "search" in search_tool.description.lower() or "busca" in search_tool.description.lower()
    assert "clause" in extract_tool.description.lower() or "cláusula" in extract_tool.description.lower()
