"""
Hybrid Search Adapter
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Implementa busca híbrida combinando BM25 (keyword) com busca semântica.
"""

import math
import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
from langchain.schema import Document

from common.logging import get_logger
from common.metrics import metrics, AuditorMetrics

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Resultado de busca com scores combinados."""
    document: Document
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    combined_score: float = 0.0
    rank: int = 0


class BM25:
    """
    Implementação do algoritmo BM25 para busca por palavras-chave.
    
    BM25 é um algoritmo de ranking que considera:
    - Frequência do termo no documento (TF)
    - Frequência do termo no corpus (IDF)
    - Tamanho do documento
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Inicializa BM25.
        
        Args:
            k1: Parâmetro de saturação de frequência (1.2-2.0)
            b: Parâmetro de normalização de tamanho (0-1)
        """
        self.k1 = k1
        self.b = b
        self.corpus: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.idf: Dict[str, float] = {}
        self.corpus_size: int = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokeniza texto em palavras."""
        # Converte para minúsculas e remove caracteres especiais
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        # Divide em palavras
        tokens = text.split()
        # Remove stopwords básicas em português
        stopwords = {
            'a', 'o', 'e', 'é', 'de', 'da', 'do', 'em', 'um', 'uma', 'para',
            'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as',
            'dos', 'como', 'mas', 'foi', 'ao', 'ele', 'das', 'tem', 'à', 'seu',
            'sua', 'ou', 'ser', 'quando', 'muito', 'há', 'nos', 'já', 'está',
            'eu', 'também', 'só', 'pelo', 'pela', 'até', 'isso', 'ela', 'entre',
            'era', 'depois', 'sem', 'mesmo', 'aos', 'ter', 'seus', 'quem',
            'nas', 'me', 'esse', 'eles', 'estão', 'você', 'tinha', 'foram',
            'essa', 'num', 'nem', 'suas', 'meu', 'às', 'minha', 'têm', 'numa',
            'pelos', 'elas', 'havia', 'seja', 'qual', 'será', 'nós', 'tenho',
            'lhe', 'deles', 'essas', 'esses', 'pelas', 'este', 'fosse', 'dele'
        }
        return [t for t in tokens if t not in stopwords and len(t) > 1]
    
    def fit(self, documents: List[Document]) -> None:
        """
        Treina o modelo BM25 com o corpus.
        
        Args:
            documents: Lista de documentos para indexar
        """
        logger.info(f"Fitting BM25 with {len(documents)} documents")
        
        self.corpus = []
        self.doc_lengths = []
        self.doc_freqs = defaultdict(int)
        
        # Tokeniza todos os documentos
        for doc in documents:
            tokens = self._tokenize(doc.page_content)
            self.corpus.append(tokens)
            self.doc_lengths.append(len(tokens))
            
            # Conta frequência de documentos para cada termo
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1
        
        self.corpus_size = len(self.corpus)
        self.avg_doc_length = sum(self.doc_lengths) / self.corpus_size if self.corpus_size > 0 else 0
        
        # Calcula IDF para cada termo
        for term, doc_freq in self.doc_freqs.items():
            self.idf[term] = math.log(
                (self.corpus_size - doc_freq + 0.5) / (doc_freq + 0.5) + 1
            )
        
        logger.info(
            "BM25 fitted",
            extra_data={
                "corpus_size": self.corpus_size,
                "vocabulary_size": len(self.doc_freqs),
                "avg_doc_length": round(self.avg_doc_length, 2)
            }
        )
    
    def _score_document(self, query_tokens: List[str], doc_idx: int) -> float:
        """Calcula score BM25 para um documento."""
        doc_tokens = self.corpus[doc_idx]
        doc_length = self.doc_lengths[doc_idx]
        
        # Conta frequência de termos no documento
        term_freqs = defaultdict(int)
        for token in doc_tokens:
            term_freqs[token] += 1
        
        score = 0.0
        for term in query_tokens:
            if term not in self.idf:
                continue
            
            tf = term_freqs.get(term, 0)
            idf = self.idf[term]
            
            # Fórmula BM25
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            
            score += idf * numerator / denominator
        
        return score
    
    def search(self, query: str, k: int = 10) -> List[Tuple[int, float]]:
        """
        Busca documentos relevantes para a query.
        
        Args:
            query: Query de busca
            k: Número de resultados
            
        Returns:
            Lista de (índice_documento, score)
        """
        if not self.corpus:
            return []
        
        query_tokens = self._tokenize(query)
        
        if not query_tokens:
            return []
        
        # Calcula score para cada documento
        scores = []
        for idx in range(self.corpus_size):
            score = self._score_document(query_tokens, idx)
            if score > 0:
                scores.append((idx, score))
        
        # Ordena por score decrescente
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:k]


class HybridSearchAdapter:
    """
    Adapter para busca híbrida combinando BM25 e busca semântica.
    
    Usa Reciprocal Rank Fusion (RRF) para combinar os resultados.
    """
    
    def __init__(
        self,
        chromadb_adapter: Any,
        alpha: float = 0.5,
        rrf_k: int = 60
    ):
        """
        Inicializa adapter de busca híbrida.
        
        Args:
            chromadb_adapter: Adapter do ChromaDB para busca semântica
            alpha: Peso da busca semântica (0-1). 0.5 = pesos iguais
            rrf_k: Parâmetro k do RRF (geralmente 60)
        """
        self._chromadb = chromadb_adapter
        self._alpha = alpha
        self._rrf_k = rrf_k
        self._bm25: Optional[BM25] = None
        self._documents: List[Document] = []
        
        logger.info(
            "HybridSearchAdapter initialized",
            extra_data={"alpha": alpha, "rrf_k": rrf_k}
        )
    
    def index_documents(self, documents: List[Document]) -> None:
        """
        Indexa documentos para busca híbrida.
        
        Args:
            documents: Lista de documentos para indexar
        """
        self._documents = documents
        
        # Treina BM25
        self._bm25 = BM25()
        self._bm25.fit(documents)
        
        logger.info(
            "Documents indexed for hybrid search",
            extra_data={"num_documents": len(documents)}
        )
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normaliza scores para [0, 1]."""
        if not scores:
            return []
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [1.0] * len(scores)
        
        return [(s - min_score) / (max_score - min_score) for s in scores]
    
    def _rrf_score(self, rank: int) -> float:
        """Calcula score RRF para um rank."""
        return 1.0 / (self._rrf_k + rank)
    
    def search(
        self,
        query: str,
        k: int = 5,
        semantic_k: int = 10,
        keyword_k: int = 10
    ) -> List[SearchResult]:
        """
        Executa busca híbrida.
        
        Args:
            query: Query de busca
            k: Número de resultados finais
            semantic_k: Resultados da busca semântica
            keyword_k: Resultados da busca por palavras-chave
            
        Returns:
            Lista de SearchResult ordenada por score combinado
        """
        if not self._documents or not self._bm25:
            logger.warning("No documents indexed for hybrid search")
            return []
        
        logger.debug(
            "Executing hybrid search",
            extra_data={"query_length": len(query), "k": k}
        )
        
        # 1. Busca semântica via ChromaDB
        semantic_results = self._chromadb.search_with_score(query, k=semantic_k)
        
        # 2. Busca BM25
        bm25_results = self._bm25.search(query, k=keyword_k)
        
        # 3. Cria mapeamento de documentos para scores
        doc_scores: Dict[int, Dict[str, Any]] = {}
        
        # Processa resultados semânticos
        for rank, (doc, score) in enumerate(semantic_results):
            # Encontra índice do documento
            doc_idx = self._find_document_index(doc)
            if doc_idx is not None:
                if doc_idx not in doc_scores:
                    doc_scores[doc_idx] = {
                        "document": doc,
                        "semantic_score": 0.0,
                        "semantic_rank": None,
                        "keyword_score": 0.0,
                        "keyword_rank": None
                    }
                doc_scores[doc_idx]["semantic_score"] = 1.0 - score  # ChromaDB retorna distância
                doc_scores[doc_idx]["semantic_rank"] = rank + 1
        
        # Processa resultados BM25
        for rank, (doc_idx, score) in enumerate(bm25_results):
            if doc_idx not in doc_scores:
                doc_scores[doc_idx] = {
                    "document": self._documents[doc_idx],
                    "semantic_score": 0.0,
                    "semantic_rank": None,
                    "keyword_score": 0.0,
                    "keyword_rank": None
                }
            doc_scores[doc_idx]["keyword_score"] = score
            doc_scores[doc_idx]["keyword_rank"] = rank + 1
        
        # 4. Combina scores usando RRF
        results = []
        for doc_idx, data in doc_scores.items():
            # Calcula RRF scores
            rrf_semantic = self._rrf_score(data["semantic_rank"]) if data["semantic_rank"] else 0
            rrf_keyword = self._rrf_score(data["keyword_rank"]) if data["keyword_rank"] else 0
            
            # Combina com pesos
            combined = self._alpha * rrf_semantic + (1 - self._alpha) * rrf_keyword
            
            results.append(SearchResult(
                document=data["document"],
                semantic_score=data["semantic_score"],
                keyword_score=data["keyword_score"],
                combined_score=combined
            ))
        
        # 5. Ordena por score combinado
        results.sort(key=lambda x: x.combined_score, reverse=True)
        
        # 6. Atribui ranks finais
        for rank, result in enumerate(results[:k]):
            result.rank = rank + 1
        
        # Registra métricas
        metrics.increment("hybrid_search_total")
        AuditorMetrics.record_vector_search(k, 0)  # Duração será medida pelo decorator
        
        logger.debug(
            "Hybrid search completed",
            extra_data={
                "semantic_results": len(semantic_results),
                "keyword_results": len(bm25_results),
                "combined_results": len(results[:k])
            }
        )
        
        return results[:k]
    
    def _find_document_index(self, doc: Document) -> Optional[int]:
        """Encontra índice do documento no corpus."""
        for idx, stored_doc in enumerate(self._documents):
            if stored_doc.page_content == doc.page_content:
                return idx
        return None
    
    async def asearch(
        self,
        query: str,
        k: int = 5,
        semantic_k: int = 10,
        keyword_k: int = 10
    ) -> List[SearchResult]:
        """Executa busca híbrida (async)."""
        if not self._documents or not self._bm25:
            return []
        
        # Busca semântica async
        semantic_results = await self._chromadb.asearch_with_score(query, k=semantic_k)
        
        # BM25 é síncrono (rápido o suficiente)
        bm25_results = self._bm25.search(query, k=keyword_k)
        
        # Processa igual ao sync
        doc_scores: Dict[int, Dict[str, Any]] = {}
        
        for rank, (doc, score) in enumerate(semantic_results):
            doc_idx = self._find_document_index(doc)
            if doc_idx is not None:
                if doc_idx not in doc_scores:
                    doc_scores[doc_idx] = {
                        "document": doc,
                        "semantic_score": 0.0,
                        "semantic_rank": None,
                        "keyword_score": 0.0,
                        "keyword_rank": None
                    }
                doc_scores[doc_idx]["semantic_score"] = 1.0 - score
                doc_scores[doc_idx]["semantic_rank"] = rank + 1
        
        for rank, (doc_idx, score) in enumerate(bm25_results):
            if doc_idx not in doc_scores:
                doc_scores[doc_idx] = {
                    "document": self._documents[doc_idx],
                    "semantic_score": 0.0,
                    "semantic_rank": None,
                    "keyword_score": 0.0,
                    "keyword_rank": None
                }
            doc_scores[doc_idx]["keyword_score"] = score
            doc_scores[doc_idx]["keyword_rank"] = rank + 1
        
        results = []
        for doc_idx, data in doc_scores.items():
            rrf_semantic = self._rrf_score(data["semantic_rank"]) if data["semantic_rank"] else 0
            rrf_keyword = self._rrf_score(data["keyword_rank"]) if data["keyword_rank"] else 0
            combined = self._alpha * rrf_semantic + (1 - self._alpha) * rrf_keyword
            
            results.append(SearchResult(
                document=data["document"],
                semantic_score=data["semantic_score"],
                keyword_score=data["keyword_score"],
                combined_score=combined
            ))
        
        results.sort(key=lambda x: x.combined_score, reverse=True)
        
        for rank, result in enumerate(results[:k]):
            result.rank = rank + 1
        
        return results[:k]
    
    def get_documents(self) -> List[Document]:
        """Retorna documentos indexados."""
        return self._documents
