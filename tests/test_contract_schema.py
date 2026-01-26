"""
Testes para Contract Schema
Auditor de Contratos - Bootcamp Itaú FIAP 2026
"""

import pytest
from pydantic import ValidationError
from domain.contract_schema import ContractMetadata


def test_contract_metadata_valid():
    """Testa criação de ContractMetadata válido."""
    metadata = ContractMetadata(
        garantia_tipo="Alienação Fiduciária",
        garantia_objeto="Imóvel Matrícula 12345",
        taxa_juros=1.0,
        prazo_meses=36,
        valor_principal=1500000.0,
        risco_legal="Baixo",
        compliance_check=True
    )
    
    assert metadata.garantia_tipo == "Alienação Fiduciária"
    assert metadata.taxa_juros == 1.0
    assert metadata.prazo_meses == 36


def test_contract_metadata_invalid_risk_level():
    """Testa que erro é levantado para risco_legal inválido."""
    with pytest.raises(ValidationError):
        ContractMetadata(
            garantia_tipo="Alienação Fiduciária",
            garantia_objeto="Imóvel",
            taxa_juros=1.0,
            prazo_meses=36,
            valor_principal=1500000.0,
            risco_legal="Altíssimo",  # Inválido
            compliance_check=True
        )


def test_contract_metadata_negative_interest_rate():
    """Testa que erro é levantado para taxa negativa."""
    with pytest.raises(ValidationError):
        ContractMetadata(
            garantia_tipo="Alienação Fiduciária",
            garantia_objeto="Imóvel",
            taxa_juros=-1.0,  # Negativo
            prazo_meses=36,
            valor_principal=1500000.0,
            risco_legal="Baixo",
            compliance_check=True
        )


def test_contract_metadata_invalid_term():
    """Testa que erro é levantado para prazo inválido."""
    with pytest.raises(ValidationError):
        ContractMetadata(
            garantia_tipo="Alienação Fiduciária",
            garantia_objeto="Imóvel",
            taxa_juros=1.0,
            prazo_meses=0,  # Zero ou negativo
            valor_principal=1500000.0,
            risco_legal="Baixo",
            compliance_check=True
        )


def test_calculate_total_amount():
    """Testa cálculo de montante total."""
    metadata = ContractMetadata(
        garantia_tipo="Alienação Fiduciária",
        garantia_objeto="Imóvel",
        taxa_juros=1.0,
        prazo_meses=36,
        valor_principal=1500000.0,
        risco_legal="Baixo",
        compliance_check=True
    )
    
    total = metadata.calculate_total_amount()
    
    assert total > metadata.valor_principal  # Deve ser maior
    assert total > 2000000.0  # Aproximadamente 2.15M


def test_calculate_total_interest():
    """Testa cálculo de juros totais."""
    metadata = ContractMetadata(
        garantia_tipo="Alienação Fiduciária",
        garantia_objeto="Imóvel",
        taxa_juros=1.0,
        prazo_meses=36,
        valor_principal=1500000.0,
        risco_legal="Baixo",
        compliance_check=True
    )
    
    juros = metadata.calculate_total_interest()
    
    assert juros > 0
    assert juros < metadata.valor_principal  # Juros não devem exceder principal para taxas razoáveis


def test_to_summary():
    """Testa geração de resumo textual."""
    metadata = ContractMetadata(
        garantia_tipo="Alienação Fiduciária",
        garantia_objeto="Imóvel",
        taxa_juros=1.0,
        prazo_meses=36,
        valor_principal=1500000.0,
        risco_legal="Baixo",
        compliance_check=True
    )
    
    summary = metadata.to_summary()
    
    assert "RESUMO DO CONTRATO" in summary
    assert "1500000" in summary
    assert "Baixo" in summary
    assert "✅ Conforme" in summary
