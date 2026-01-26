"""
Contract Schema - Modelos Pydantic
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Define os schemas de dados para contratos usando Pydantic para validação.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from common.types import RiskLevel


class ContractMetadata(BaseModel):
    """
    Schema Pydantic para metadados extraídos de contratos bancários.
    
    Todos os campos são validados automaticamente pelo Pydantic.
    """
    
    garantia_tipo: str = Field(
        description="Tipo de garantia (ex: 'Alienação Fiduciária', 'Fiança', 'Penhor')",
        min_length=3,
        max_length=100
    )
    
    garantia_objeto: str = Field(
        description="Objeto dado em garantia (ex: 'Imóvel Matrícula 12345')",
        min_length=3,
        max_length=200
    )
    
    taxa_juros: float = Field(
        description="Taxa de juros mensal em percentual (ex: 1.0 para 1%)",
        ge=0.0,
        le=10.0
    )
    
    prazo_meses: int = Field(
        description="Prazo do contrato em meses",
        ge=1,
        le=600  # 50 anos máximo
    )
    
    valor_principal: float = Field(
        description="Valor principal do contrato em reais",
        ge=0.0
    )
    
    risco_legal: str = Field(
        description="Classificação de risco: 'Baixo', 'Médio' ou 'Alto'"
    )
    
    compliance_check: bool = Field(
        description="True se contrato está em compliance com políticas do banco"
    )
    
    # Campos opcionais adicionais
    observacoes: Optional[str] = Field(
        default=None,
        description="Observações adicionais sobre o contrato"
    )
    
    @field_validator('risco_legal')
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        """Valida se o nível de risco está entre os valores permitidos."""
        allowed = [RiskLevel.BAIXO.value, RiskLevel.MEDIO.value, RiskLevel.ALTO.value]
        if v not in allowed:
            raise ValueError(
                f"risco_legal deve ser um de: {', '.join(allowed)}. Recebido: {v}"
            )
        return v
    
    @field_validator('taxa_juros')
    @classmethod
    def validate_interest_rate(cls, v: float) -> float:
        """Valida se a taxa de juros está em um range razoável."""
        if v < 0.1:
            raise ValueError("Taxa de juros muito baixa (< 0.1%)")
        if v > 5.0:
            # Warning mas não erro - pode ser juros alto legítimo
            pass
        return v
    
    def calculate_total_amount(self) -> float:
        """
        Calcula o montante total do contrato com juros compostos.
        
        Fórmula: M = P * (1 + i)^n
        onde:
        - M = montante final
        - P = valor principal
        - i = taxa de juros mensal (em decimal)
        - n = número de meses
        """
        i = self.taxa_juros / 100  # Converter de percentual para decimal
        montante = self.valor_principal * ((1 + i) ** self.prazo_meses)
        return montante
    
    def calculate_total_interest(self) -> float:
        """Calcula o total de juros pagos."""
        return self.calculate_total_amount() - self.valor_principal
    
    def to_summary(self) -> str:
        """Retorna um resumo textual do contrato."""
        total = self.calculate_total_amount()
        juros = self.calculate_total_interest()
        
        return f"""
📄 RESUMO DO CONTRATO

💰 Financeiro:
   • Valor Principal: R$ {self.valor_principal:,.2f}
   • Taxa de Juros: {self.taxa_juros}% ao mês
   • Prazo: {self.prazo_meses} meses
   • Montante Total: R$ {total:,.2f}
   • Juros Totais: R$ {juros:,.2f}

🔒 Garantia:
   • Tipo: {self.garantia_tipo}
   • Objeto: {self.garantia_objeto}

⚖️ Análise:
   • Risco Legal: {self.risco_legal}
   • Compliance: {'✅ Conforme' if self.compliance_check else '❌ Não conforme'}

{f'📝 Observações: {self.observacoes}' if self.observacoes else ''}
        """.strip()
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "garantia_tipo": "Alienação Fiduciária",
                    "garantia_objeto": "Imóvel Matrícula 12345 do 2º CRI São Paulo",
                    "taxa_juros": 1.0,
                    "prazo_meses": 36,
                    "valor_principal": 1500000.0,
                    "risco_legal": "Baixo",
                    "compliance_check": True,
                    "observacoes": "Contrato padrão de mútuo conversível"
                }
            ]
        }
    }
