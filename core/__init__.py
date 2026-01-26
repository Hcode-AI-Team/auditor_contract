"""
Core Layer - Lógica Principal
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Este módulo contém a lógica principal da aplicação:
- Agente ReAct
- Configurações
- Sistema de memória (futuro)
"""

from .agent import AuditorAgent
from .config import Config

__all__ = [
    "AuditorAgent",
    "Config",
]
