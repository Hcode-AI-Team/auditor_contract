"""
ChromaDB Adapter
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Adapter para integração com ChromaDB (Vector Store) com suporte async.
"""

import time
import asyncio
from typing import List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from langchain_chroma import Chroma
from langchain.schema import Document

from common.exceptions import VectorStoreError
from common.types import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_PERSIST_DIRECTORY,
    DEFAULT_RETRIEVAL_K,
    BaseAdapter,
    EmbeddingsProtocol,
    SearchResult
)
from common.logging import get_logger, log_execution_time
from common.metrics import metrics, AuditorMetrics

logger = get_logger(__name__)


class ChromaDBAdapter(BaseAdapter):
    """
    Adapter para ChromaDB com suporte async.
    
    Implementa:
    - Busca por similaridade
    - Logging estruturado
    - Métricas de performance
    - Suporte sync e async
    """
    
    def __init__(
        self,
        embeddings: EmbeddingsProtocol,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        persist_directory: str = DEFAULT_PERSIST_DIRECTORY
    ) -> None:
        """
        Inicializa adapter do ChromaDB.
        
        Args:
            embeddings: Cliente de embeddings (OpenAIEmbeddings ou compatível)
            collection_name: Nome da coleção no ChromaDB
            persist_directory: Diretório para persistir o banco
        """
        self._embeddings: EmbeddingsProtocol = embeddings
        self._collection_name: str = collection_name
        self._persist_directory: str = persist_directory
        self._vectorstore: Optional[Chroma] = None
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=4)
        
        logger.info(
            "ChromaDB Adapter initialized",
            extra_data={
                "collection_name": collection_name,
                "persist_directory": persist_directory
            }
        )
    
    @property
    def embeddings(self) -> EmbeddingsProtocol:
        """Embeddings em uso."""
        return self._embeddings
    
    @property
    def collection_name(self) -> str:
        """Nome da coleção."""
        return self._collection_name
    
    @property
    def persist_directory(self) -> str:
        """Diretório de persistência."""
        return self._persist_directory
    
    @property
    def vectorstore(self) -> Chroma:
        """
        Retorna instância do vectorstore.
        
        Raises:
            VectorStoreError: Se vectorstore não foi inicializado
        """
        if self._vectorstore is None:
            raise VectorStoreError(
                "Vectorstore não inicializado. Chame create_from_documents() primeiro."
            )
        return self._vectorstore
    
    # ========================================================================
    # SYNC METHODS
    # ========================================================================
    
    @log_execution_time()
    def create_from_documents(self, documents: List[Document]) -> None:
        """
        Cria vectorstore a partir de documentos.
        
        Args:
            documents: Lista de documentos (já em chunks)
            
        Raises:
            VectorStoreError: Se houver erro ao criar vectorstore
        """
        start_time = time.perf_counter()
        try:
            logger.info(
                "Creating vectorstore from documents",
                extra_data={"num_documents": len(documents)}
            )
            
            self._vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self._embeddings,
                collection_name=self._collection_name,
                persist_directory=self._persist_directory
            )
            
            duration = time.perf_counter() - start_time
            metrics.increment(AuditorMetrics.CHUNKS_INDEXED, value=len(documents))
            metrics.set_gauge(AuditorMetrics.VECTORSTORE_SIZE, len(documents))
            
            logger.info(
                "Vectorstore created successfully",
                extra_data={
                    "collection": self._collection_name,
                    "num_documents": len(documents),
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
        except Exception as e:
            logger.error(
                "Error creating vectorstore",
                extra_data={"num_documents": len(documents), "error": str(e)}
            )
            raise VectorStoreError(
                f"Erro ao criar vectorstore: {str(e)}",
                details={
                    "num_documents": len(documents),
                    "collection": self._collection_name
                }
            )
    
    @log_execution_time()
    def load_existing(self) -> None:
        """
        Carrega vectorstore existente do disco.
        
        Raises:
            VectorStoreError: Se não encontrar vectorstore existente
        """
        try:
            logger.info(
                "Loading existing vectorstore",
                extra_data={"collection": self._collection_name}
            )
            
            self._vectorstore = Chroma(
                embedding_function=self._embeddings,
                collection_name=self._collection_name,
                persist_directory=self._persist_directory
            )
            
            logger.info(
                "Vectorstore loaded successfully",
                extra_data={"collection": self._collection_name}
            )
            
        except Exception as e:
            logger.error(
                "Error loading vectorstore",
                extra_data={"collection": self._collection_name, "error": str(e)}
            )
            raise VectorStoreError(
                f"Erro ao carregar vectorstore: {str(e)}",
                details={"collection": self._collection_name}
            )
    
    @log_execution_time()
    def search(self, query: str, k: int = DEFAULT_RETRIEVAL_K) -> List[Document]:
        """
        Busca documentos por similaridade semântica.
        
        Args:
            query: Query de busca
            k: Número de resultados a retornar
            
        Returns:
            Lista de documentos mais relevantes
            
        Raises:
            VectorStoreError: Se houver erro na busca
        """
        start_time = time.perf_counter()
        try:
            logger.debug(
                "Searching vectorstore",
                extra_data={"query_length": len(query), "k": k}
            )
            
            results = self.vectorstore.similarity_search(query, k=k)
            
            duration = time.perf_counter() - start_time
            AuditorMetrics.record_vector_search(k, duration)
            
            logger.debug(
                "Search completed",
                extra_data={
                    "num_results": len(results),
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Error searching vectorstore",
                extra_data={"query": query[:100], "error": str(e)}
            )
            raise VectorStoreError(
                f"Erro ao buscar no vectorstore: {str(e)}",
                details={"query": query[:100], "k": k}
            )
    
    @log_execution_time()
    def search_with_score(
        self,
        query: str,
        k: int = DEFAULT_RETRIEVAL_K
    ) -> List[Tuple[Document, float]]:
        """
        Busca documentos com scores de similaridade.
        
        Args:
            query: Query de busca
            k: Número de resultados a retornar
            
        Returns:
            Lista de tuplas (documento, score)
        """
        start_time = time.perf_counter()
        try:
            logger.debug(
                "Searching vectorstore with scores",
                extra_data={"query_length": len(query), "k": k}
            )
            
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            duration = time.perf_counter() - start_time
            AuditorMetrics.record_vector_search(k, duration)
            
            logger.debug(
                "Search with scores completed",
                extra_data={
                    "num_results": len(results),
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Error searching vectorstore with score",
                extra_data={"query": query[:100], "error": str(e)}
            )
            raise VectorStoreError(
                f"Erro ao buscar com score: {str(e)}",
                details={"query": query[:100], "k": k}
            )
    
    @log_execution_time()
    def add_documents(self, documents: List[Document]) -> None:
        """
        Adiciona novos documentos ao vectorstore existente.
        
        Args:
            documents: Lista de documentos para adicionar
        """
        try:
            logger.info(
                "Adding documents to vectorstore",
                extra_data={"num_documents": len(documents)}
            )
            
            self.vectorstore.add_documents(documents)
            
            metrics.increment(AuditorMetrics.CHUNKS_INDEXED, value=len(documents))
            
            logger.info(
                "Documents added successfully",
                extra_data={"num_documents": len(documents)}
            )
            
        except Exception as e:
            logger.error(
                "Error adding documents",
                extra_data={"num_documents": len(documents), "error": str(e)}
            )
            raise VectorStoreError(
                f"Erro ao adicionar documentos: {str(e)}",
                details={"num_documents": len(documents)}
            )
    
    def delete_collection(self) -> None:
        """
        Deleta a coleção do ChromaDB.
        
        Útil para limpar dados antigos.
        """
        try:
            if self._vectorstore:
                logger.info(
                    "Deleting collection",
                    extra_data={"collection": self._collection_name}
                )
                self._vectorstore.delete_collection()
                self._vectorstore = None
                metrics.set_gauge(AuditorMetrics.VECTORSTORE_SIZE, 0)
                logger.info("Collection deleted successfully")
        except Exception as e:
            logger.error(
                "Error deleting collection",
                extra_data={"collection": self._collection_name, "error": str(e)}
            )
            raise VectorStoreError(
                f"Erro ao deletar coleção: {str(e)}",
                details={"collection": self._collection_name}
            )
    
    # ========================================================================
    # ASYNC METHODS
    # ========================================================================
    
    async def acreate_from_documents(self, documents: List[Document]) -> None:
        """Cria vectorstore a partir de documentos (async)."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            self.create_from_documents,
            documents
        )
    
    async def aload_existing(self) -> None:
        """Carrega vectorstore existente do disco (async)."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self.load_existing)
    
    async def asearch(self, query: str, k: int = DEFAULT_RETRIEVAL_K) -> List[Document]:
        """Busca documentos por similaridade semântica (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.search(query, k)
        )
    
    async def asearch_with_score(
        self,
        query: str,
        k: int = DEFAULT_RETRIEVAL_K
    ) -> List[Tuple[Document, float]]:
        """Busca documentos com scores de similaridade (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.search_with_score(query, k)
        )
    
    async def aadd_documents(self, documents: List[Document]) -> None:
        """Adiciona novos documentos ao vectorstore existente (async)."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            self.add_documents,
            documents
        )
    
    # ========================================================================
    # HEALTH CHECK
    # ========================================================================
    
    def health_check(self) -> bool:
        """Verifica se o adapter está saudável."""
        try:
            if self._vectorstore is None:
                return False
            # Tenta fazer uma busca simples
            self.search("test", k=1)
            logger.info("ChromaDB Adapter health check passed")
            return True
        except Exception as e:
            logger.warning(
                "ChromaDB Adapter health check failed",
                extra_data={"error": str(e)}
            )
            return False
    
    async def ahealth_check(self) -> bool:
        """Verifica se o adapter está saudável (async)."""
        try:
            if self._vectorstore is None:
                return False
            await self.asearch("test", k=1)
            logger.info("ChromaDB Adapter health check passed (async)")
            return True
        except Exception as e:
            logger.warning(
                "ChromaDB Adapter health check failed (async)",
                extra_data={"error": str(e)}
            )
            return False
    
    def __del__(self) -> None:
        """Cleanup ao destruir o objeto."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)