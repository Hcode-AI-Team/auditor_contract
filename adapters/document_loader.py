"""
Document Loader
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Carrega e processa documentos (PDF/TXT) para ingestão no vectorstore.
"""

import os
import asyncio
from typing import List, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from common.exceptions import DocumentLoadError
from common.types import (
    DocumentType,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP
)
from common.logging import get_logger, log_execution_time
from common.metrics import metrics

logger = get_logger(__name__)


class DocumentLoader:
    """
    Carrega e processa documentos com suporte a PDF e TXT.
    
    Implementa:
    - Chunking com RecursiveCharacterTextSplitter
    - Logging estruturado
    - Suporte sync e async
    """
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ) -> None:
        """
        Inicializa document loader.
        
        Args:
            chunk_size: Tamanho de cada chunk em caracteres
            chunk_overlap: Quantidade de caracteres sobrepostos entre chunks
        """
        self._chunk_size: int = chunk_size
        self._chunk_overlap: int = chunk_overlap
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=2)
        
        # Configura text splitter
        self._text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
        
        logger.info(
            "DocumentLoader initialized",
            extra_data={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}
        )
    
    @property
    def chunk_size(self) -> int:
        """Tamanho do chunk."""
        return self._chunk_size
    
    @property
    def chunk_overlap(self) -> int:
        """Sobreposição entre chunks."""
        return self._chunk_overlap
    
    @property
    def text_splitter(self) -> RecursiveCharacterTextSplitter:
        """Text splitter configurado."""
        return self._text_splitter
    
    def _detect_document_type(self, file_path: str) -> DocumentType:
        """
        Detecta tipo do documento pela extensão.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            DocumentType enum
            
        Raises:
            DocumentLoadError: Se extensão não suportada
        """
        ext = Path(file_path).suffix.lower()
        
        if ext == ".pdf":
            return DocumentType.PDF
        elif ext == ".txt":
            return DocumentType.TXT
        else:
            logger.error(
                "Unsupported file type",
                extra_data={"file_path": file_path, "extension": ext}
            )
            raise DocumentLoadError(
                f"Tipo de arquivo não suportado: {ext}",
                details={"file_path": file_path, "extension": ext}
            )
    
    @log_execution_time()
    def load_document(self, file_path: str) -> List[Document]:
        """
        Carrega documento do disco.
        
        Args:
            file_path: Caminho para o arquivo
            
        Returns:
            Lista de documentos (páginas)
            
        Raises:
            DocumentLoadError: Se houver erro ao carregar
        """
        # Verifica se arquivo existe
        if not os.path.exists(file_path):
            logger.error(
                "File not found",
                extra_data={"file_path": file_path}
            )
            raise DocumentLoadError(
                f"Arquivo não encontrado: {file_path}",
                details={"file_path": file_path}
            )
        
        # Detecta tipo e escolhe loader
        doc_type = self._detect_document_type(file_path)
        
        try:
            logger.info(
                "Loading document",
                extra_data={"file_path": file_path, "type": doc_type.value}
            )
            
            if doc_type == DocumentType.PDF:
                loader = PyPDFLoader(file_path)
            else:  # TXT
                loader = TextLoader(file_path, encoding='utf-8')
            
            documents = loader.load()
            
            logger.info(
                "Document loaded successfully",
                extra_data={
                    "file_path": file_path,
                    "num_pages": len(documents)
                }
            )
            
            return documents
            
        except Exception as e:
            logger.error(
                "Error loading document",
                extra_data={"file_path": file_path, "error": str(e)}
            )
            raise DocumentLoadError(
                f"Erro ao carregar documento: {str(e)}",
                details={"file_path": file_path, "type": doc_type.value}
            )
    
    @log_execution_time()
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Divide documentos em chunks.
        
        Args:
            documents: Lista de documentos para dividir
            
        Returns:
            Lista de chunks (documentos menores)
        """
        try:
            logger.debug(
                "Splitting documents into chunks",
                extra_data={"num_documents": len(documents)}
            )
            
            chunks = self._text_splitter.split_documents(documents)
            
            logger.info(
                "Documents split into chunks",
                extra_data={
                    "num_chunks": len(chunks),
                    "chunk_size": self._chunk_size,
                    "chunk_overlap": self._chunk_overlap
                }
            )
            
            return chunks
            
        except Exception as e:
            logger.error(
                "Error splitting documents",
                extra_data={"num_documents": len(documents), "error": str(e)}
            )
            raise DocumentLoadError(
                f"Erro ao dividir documento em chunks: {str(e)}",
                details={
                    "num_documents": len(documents),
                    "chunk_size": self._chunk_size
                }
            )
    
    @log_execution_time()
    def process_document(self, file_path: str) -> List[Document]:
        """
        Processa documento completo: carrega + divide em chunks.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Lista de chunks prontos para indexação
        """
        logger.info(
            "Processing document",
            extra_data={"file_path": file_path}
        )
        
        # Carrega documento
        documents = self.load_document(file_path)
        
        # Divide em chunks
        chunks = self.split_documents(documents)
        
        logger.info(
            "Document processing complete",
            extra_data={
                "file_path": file_path,
                "num_chunks": len(chunks)
            }
        )
        
        return chunks
    
    def process_multiple_documents(self, file_paths: List[str]) -> List[Document]:
        """
        Processa múltiplos documentos.
        
        Args:
            file_paths: Lista de caminhos de arquivos
            
        Returns:
            Lista de todos os chunks de todos os documentos
        """
        all_chunks: List[Document] = []
        successful = 0
        failed = 0
        
        for file_path in file_paths:
            try:
                chunks = self.process_document(file_path)
                all_chunks.extend(chunks)
                successful += 1
            except DocumentLoadError as e:
                logger.warning(
                    "Failed to process document",
                    extra_data={"file_path": file_path, "error": str(e)}
                )
                failed += 1
                continue
        
        logger.info(
            "Multiple documents processed",
            extra_data={
                "total_files": len(file_paths),
                "successful": successful,
                "failed": failed,
                "total_chunks": len(all_chunks)
            }
        )
        
        return all_chunks
    
    # ========================================================================
    # ASYNC METHODS
    # ========================================================================
    
    async def aload_document(self, file_path: str) -> List[Document]:
        """Carrega documento do disco (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.load_document,
            file_path
        )
    
    async def asplit_documents(self, documents: List[Document]) -> List[Document]:
        """Divide documentos em chunks (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.split_documents,
            documents
        )
    
    async def aprocess_document(self, file_path: str) -> List[Document]:
        """Processa documento completo (async)."""
        documents = await self.aload_document(file_path)
        return await self.asplit_documents(documents)
    
    async def aprocess_multiple_documents(self, file_paths: List[str]) -> List[Document]:
        """Processa múltiplos documentos em paralelo (async)."""
        tasks = [self.aprocess_document(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_chunks: List[Document] = []
        successful = 0
        failed = 0
        
        for result in results:
            if isinstance(result, Exception):
                failed += 1
                logger.warning(
                    "Failed to process document (async)",
                    extra_data={"error": str(result)}
                )
            else:
                all_chunks.extend(result)
                successful += 1
        
        logger.info(
            "Multiple documents processed (async)",
            extra_data={
                "total_files": len(file_paths),
                "successful": successful,
                "failed": failed,
                "total_chunks": len(all_chunks)
            }
        )
        
        return all_chunks
    
    def __del__(self) -> None:
        """Cleanup ao destruir o objeto."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)