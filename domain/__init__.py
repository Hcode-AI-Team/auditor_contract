"""
Domain Layer - Modelos de Domínio
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Este módulo contém os modelos de domínio da aplicação:
- Schemas Pydantic
- Definição de Tools
"""

from .contract_schema import ContractMetadata
from .tools import create_contract_tools

__all__ = [
    "ContractMetadata",
    "create_contract_tools",
]
