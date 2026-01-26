"""
Adapters Layer - Integrações Externas
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Este módulo contém adapters para serviços externos:
- OpenAI (LLM e Embeddings)
- ChromaDB (Vector Store)
- Document Loaders (PDF/TXT)
- Hybrid Search (BM25 + Semântico)
"""

from .openai_adapter import OpenAIAdapter
from .chromadb_adapter import ChromaDBAdapter
from .document_loader import DocumentLoader
from .hybrid_search import HybridSearchAdapter, BM25, SearchResult

__all__ = [
    "OpenAIAdapter",
    "ChromaDBAdapter",
    "DocumentLoader",
    "HybridSearchAdapter",
    "BM25",
    "SearchResult",
]
