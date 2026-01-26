"""
OpenAI Adapter
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Adapter para integração com OpenAI (LLM e Embeddings) com suporte async.
"""

import time
from typing import Optional, List, Any
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import BaseMessage

from common.exceptions import ConfigurationError, EmbeddingError, LLMError
from common.types import (
    DEFAULT_LLM_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_TEMPERATURE,
    OPENAI_TIMEOUT,
    BaseAdapter,
    EmbeddingsProtocol,
    LLMProtocol
)
from common.logging import get_logger, log_execution_time
from common.metrics import metrics, AuditorMetrics
from common.retry import retry_with_backoff, RETRY_CONFIG_OPENAI
from common.cache import get_embedding_cache

logger = get_logger(__name__)

# Exceções que devem triggerar retry
OPENAI_RETRYABLE_EXCEPTIONS = (
    TimeoutError,
    ConnectionError,
    # OpenAI specific errors são capturadas pelo LangChain
)


class OpenAIAdapter(BaseAdapter):
    """
    Adapter para serviços da OpenAI com suporte completo a async.
    
    Implementa:
    - Lazy loading de recursos
    - Logging estruturado
    - Métricas de performance
    - Suporte sync e async
    """
    
    def __init__(
        self,
        api_key: str,
        llm_model: str = DEFAULT_LLM_MODEL,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        streaming: bool = True,
        timeout: int = OPENAI_TIMEOUT
    ) -> None:
        """
        Inicializa adapter da OpenAI.
        
        Args:
            api_key: Chave API da OpenAI
            llm_model: Nome do modelo LLM
            embedding_model: Nome do modelo de embeddings
            temperature: Temperatura do LLM (0 = determinístico)
            streaming: Se deve usar streaming nas respostas
            timeout: Timeout para requisições em segundos
            
        Raises:
            ConfigurationError: Se API key for inválida
        """
        if not api_key or not api_key.startswith("sk-"):
            logger.error(
                "API Key da OpenAI inválida",
                extra_data={"api_key_prefix": api_key[:10] if api_key else None}
            )
            raise ConfigurationError(
                "API Key da OpenAI inválida",
                details={"api_key_prefix": api_key[:10] if api_key else None}
            )
        
        self._api_key: str = api_key
        self._llm_model: str = llm_model
        self._embedding_model: str = embedding_model
        self._temperature: float = temperature
        self._streaming: bool = streaming
        self._timeout: int = timeout
        
        # Lazy loaded instances
        self._llm: Optional[ChatOpenAI] = None
        self._embeddings: Optional[OpenAIEmbeddings] = None
        
        logger.info(
            "OpenAI Adapter initialized",
            extra_data={
                "llm_model": llm_model,
                "embedding_model": embedding_model,
                "temperature": temperature
            }
        )
    
    @property
    def api_key(self) -> str:
        """API key (somente leitura)."""
        return self._api_key
    
    @property
    def llm_model(self) -> str:
        """Modelo LLM em uso."""
        return self._llm_model
    
    @property
    def embedding_model(self) -> str:
        """Modelo de embeddings em uso."""
        return self._embedding_model
    
    @property
    def temperature(self) -> float:
        """Temperatura do LLM."""
        return self._temperature
    
    @property
    def llm(self) -> ChatOpenAI:
        """
        Retorna instância do LLM (lazy loading).
        
        Returns:
            Cliente ChatOpenAI configurado
        """
        if self._llm is None:
            logger.debug("Creating ChatOpenAI instance")
            self._llm = ChatOpenAI(
                model=self._llm_model,
                temperature=self._temperature,
                streaming=self._streaming,
                api_key=self._api_key,
                request_timeout=self._timeout
            )
        return self._llm
    
    @property
    def embeddings(self) -> OpenAIEmbeddings:
        """
        Retorna instância do embeddings (lazy loading).
        
        Returns:
            Cliente OpenAIEmbeddings configurado
        """
        if self._embeddings is None:
            logger.debug("Creating OpenAIEmbeddings instance")
            self._embeddings = OpenAIEmbeddings(
                model=self._embedding_model,
                api_key=self._api_key,
                request_timeout=self._timeout
            )
        return self._embeddings
    
    # ========================================================================
    # SYNC METHODS
    # ========================================================================
    
    @log_execution_time()
    @retry_with_backoff(**RETRY_CONFIG_OPENAI)
    def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Gera embedding para um texto.
        
        Args:
            text: Texto para embedar
            use_cache: Se deve usar cache de embeddings
            
        Returns:
            Lista de floats representando o embedding
            
        Raises:
            EmbeddingError: Se houver erro ao gerar embedding
        """
        # Verifica cache primeiro
        if use_cache:
            cache = get_embedding_cache(self._embedding_model)
            cached = cache.get(text)
            if cached is not None:
                logger.debug("Embedding cache hit", extra_data={"text_length": len(text)})
                return cached
        
        start_time = time.perf_counter()
        try:
            logger.debug(
                "Generating embedding for text",
                extra_data={"text_length": len(text)}
            )
            
            result = self.embeddings.embed_query(text)
            
            duration = time.perf_counter() - start_time
            AuditorMetrics.record_embeddings(1, duration, self._embedding_model)
            
            # Armazena no cache
            if use_cache:
                cache = get_embedding_cache(self._embedding_model)
                cache.set(text, result)
            
            logger.debug(
                "Embedding generated",
                extra_data={
                    "text_length": len(text),
                    "embedding_dim": len(result),
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error generating embedding",
                extra_data={"text_length": len(text), "error": str(e)}
            )
            raise EmbeddingError(
                f"Erro ao gerar embedding: {str(e)}",
                details={"text_length": len(text)}
            )
    
    @log_execution_time()
    @retry_with_backoff(**RETRY_CONFIG_OPENAI)
    def embed_documents(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        Gera embeddings para múltiplos textos.
        
        Args:
            texts: Lista de textos para embedar
            use_cache: Se deve usar cache de embeddings
            
        Returns:
            Lista de embeddings
            
        Raises:
            EmbeddingError: Se houver erro ao gerar embeddings
        """
        # Verifica cache para cada texto
        results: List[List[float]] = []
        texts_to_embed: List[str] = []
        cached_indices: List[int] = []
        
        if use_cache:
            cache = get_embedding_cache(self._embedding_model)
            for i, text in enumerate(texts):
                cached = cache.get(text)
                if cached is not None:
                    results.append(cached)
                    cached_indices.append(i)
                else:
                    texts_to_embed.append(text)
        else:
            texts_to_embed = texts
        
        if not texts_to_embed:
            logger.debug(f"All {len(texts)} embeddings from cache")
            return results
        
        start_time = time.perf_counter()
        try:
            logger.info(
                "Generating embeddings for documents",
                extra_data={
                    "num_texts": len(texts),
                    "from_cache": len(cached_indices),
                    "to_generate": len(texts_to_embed)
                }
            )
            
            new_embeddings = self.embeddings.embed_documents(texts_to_embed)
            
            duration = time.perf_counter() - start_time
            AuditorMetrics.record_embeddings(len(texts_to_embed), duration, self._embedding_model)
            
            # Armazena novos no cache
            if use_cache:
                cache = get_embedding_cache(self._embedding_model)
                for text, embedding in zip(texts_to_embed, new_embeddings):
                    cache.set(text, embedding)
            
            # Reconstrói lista na ordem original
            if use_cache and cached_indices:
                final_results: List[List[float]] = []
                new_idx = 0
                cache_idx = 0
                for i in range(len(texts)):
                    if cache_idx < len(cached_indices) and i == cached_indices[cache_idx]:
                        final_results.append(results[cache_idx])
                        cache_idx += 1
                    else:
                        final_results.append(new_embeddings[new_idx])
                        new_idx += 1
                results = final_results
            else:
                results = new_embeddings
            
            logger.info(
                "Embeddings generated",
                extra_data={
                    "num_texts": len(texts),
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Error generating embeddings",
                extra_data={"num_texts": len(texts), "error": str(e)}
            )
            raise EmbeddingError(
                f"Erro ao gerar embeddings: {str(e)}",
                details={"num_texts": len(texts)}
            )
    
    @log_execution_time()
    @retry_with_backoff(**RETRY_CONFIG_OPENAI)
    def invoke(self, messages: List[BaseMessage]) -> Any:
        """
        Invoca o LLM com mensagens.
        
        Args:
            messages: Lista de mensagens para o LLM
            
        Returns:
            Resposta do LLM
            
        Raises:
            LLMError: Se houver erro na invocação
        """
        start_time = time.perf_counter()
        try:
            logger.debug(
                "Invoking LLM",
                extra_data={"num_messages": len(messages)}
            )
            
            result = self.llm.invoke(messages)
            
            duration = time.perf_counter() - start_time
            # Estima tokens (aproximação)
            total_chars = sum(len(str(m.content)) for m in messages)
            estimated_tokens = total_chars // 4
            
            AuditorMetrics.record_llm_request(
                self._llm_model,
                estimated_tokens,
                duration
            )
            
            logger.debug(
                "LLM invocation complete",
                extra_data={
                    "duration_ms": round(duration * 1000, 2),
                    "estimated_tokens": estimated_tokens
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error invoking LLM",
                extra_data={"error": str(e)}
            )
            raise LLMError(
                f"Erro ao invocar LLM: {str(e)}",
                details={"model": self._llm_model}
            )
    
    # ========================================================================
    # ASYNC METHODS
    # ========================================================================
    
    @retry_with_backoff(**RETRY_CONFIG_OPENAI)
    async def aembed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Gera embedding para um texto (async).
        
        Args:
            text: Texto para embedar
            use_cache: Se deve usar cache de embeddings
            
        Returns:
            Lista de floats representando o embedding
            
        Raises:
            EmbeddingError: Se houver erro ao gerar embedding
        """
        # Verifica cache primeiro
        if use_cache:
            cache = get_embedding_cache(self._embedding_model)
            cached = cache.get(text)
            if cached is not None:
                logger.debug("Embedding cache hit (async)", extra_data={"text_length": len(text)})
                return cached
        
        start_time = time.perf_counter()
        try:
            logger.debug(
                "Generating embedding for text (async)",
                extra_data={"text_length": len(text)}
            )
            
            result = await self.embeddings.aembed_query(text)
            
            duration = time.perf_counter() - start_time
            AuditorMetrics.record_embeddings(1, duration, self._embedding_model)
            
            # Armazena no cache
            if use_cache:
                cache = get_embedding_cache(self._embedding_model)
                cache.set(text, result)
            
            logger.debug(
                "Embedding generated (async)",
                extra_data={
                    "text_length": len(text),
                    "embedding_dim": len(result),
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error generating embedding (async)",
                extra_data={"text_length": len(text), "error": str(e)}
            )
            raise EmbeddingError(
                f"Erro ao gerar embedding: {str(e)}",
                details={"text_length": len(text)}
            )
    
    @retry_with_backoff(**RETRY_CONFIG_OPENAI)
    async def aembed_documents(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        Gera embeddings para múltiplos textos (async).
        
        Args:
            texts: Lista de textos para embedar
            use_cache: Se deve usar cache de embeddings
            
        Returns:
            Lista de embeddings
            
        Raises:
            EmbeddingError: Se houver erro ao gerar embeddings
        """
        # Verifica cache para cada texto
        results: List[List[float]] = []
        texts_to_embed: List[str] = []
        cached_indices: List[int] = []
        
        if use_cache:
            cache = get_embedding_cache(self._embedding_model)
            for i, text in enumerate(texts):
                cached = cache.get(text)
                if cached is not None:
                    results.append(cached)
                    cached_indices.append(i)
                else:
                    texts_to_embed.append(text)
        else:
            texts_to_embed = texts
        
        if not texts_to_embed:
            logger.debug(f"All {len(texts)} embeddings from cache (async)")
            return results
        
        start_time = time.perf_counter()
        try:
            logger.info(
                "Generating embeddings for documents (async)",
                extra_data={
                    "num_texts": len(texts),
                    "from_cache": len(cached_indices),
                    "to_generate": len(texts_to_embed)
                }
            )
            
            new_embeddings = await self.embeddings.aembed_documents(texts_to_embed)
            
            duration = time.perf_counter() - start_time
            AuditorMetrics.record_embeddings(len(texts_to_embed), duration, self._embedding_model)
            
            # Armazena novos no cache
            if use_cache:
                cache = get_embedding_cache(self._embedding_model)
                for text, embedding in zip(texts_to_embed, new_embeddings):
                    cache.set(text, embedding)
            
            # Reconstrói lista na ordem original
            if use_cache and cached_indices:
                final_results: List[List[float]] = []
                new_idx = 0
                cache_idx = 0
                for i in range(len(texts)):
                    if cache_idx < len(cached_indices) and i == cached_indices[cache_idx]:
                        final_results.append(results[cache_idx])
                        cache_idx += 1
                    else:
                        final_results.append(new_embeddings[new_idx])
                        new_idx += 1
                results = final_results
            else:
                results = new_embeddings
            
            logger.info(
                "Embeddings generated (async)",
                extra_data={
                    "num_texts": len(texts),
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Error generating embeddings (async)",
                extra_data={"num_texts": len(texts), "error": str(e)}
            )
            raise EmbeddingError(
                f"Erro ao gerar embeddings: {str(e)}",
                details={"num_texts": len(texts)}
            )
    
    @retry_with_backoff(**RETRY_CONFIG_OPENAI)
    async def ainvoke(self, messages: List[BaseMessage]) -> Any:
        """
        Invoca o LLM com mensagens (async).
        
        Args:
            messages: Lista de mensagens para o LLM
            
        Returns:
            Resposta do LLM
            
        Raises:
            LLMError: Se houver erro na invocação
        """
        start_time = time.perf_counter()
        try:
            logger.debug(
                "Invoking LLM (async)",
                extra_data={"num_messages": len(messages)}
            )
            
            result = await self.llm.ainvoke(messages)
            
            duration = time.perf_counter() - start_time
            total_chars = sum(len(str(m.content)) for m in messages)
            estimated_tokens = total_chars // 4
            
            AuditorMetrics.record_llm_request(
                self._llm_model,
                estimated_tokens,
                duration
            )
            
            logger.debug(
                "LLM invocation complete (async)",
                extra_data={
                    "duration_ms": round(duration * 1000, 2),
                    "estimated_tokens": estimated_tokens
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error invoking LLM (async)",
                extra_data={"error": str(e)}
            )
            raise LLMError(
                f"Erro ao invocar LLM: {str(e)}",
                details={"model": self._llm_model}
            )
    
    # ========================================================================
    # HEALTH CHECK
    # ========================================================================
    
    def health_check(self) -> bool:
        """
        Verifica se o adapter está saudável.
        
        Returns:
            True se saudável, False caso contrário
        """
        try:
            # Tenta gerar embedding simples
            self.embed_text("test")
            logger.info("OpenAI Adapter health check passed")
            return True
        except Exception as e:
            logger.warning(
                "OpenAI Adapter health check failed",
                extra_data={"error": str(e)}
            )
            return False
    
    async def ahealth_check(self) -> bool:
        """
        Verifica se o adapter está saudável (async).
        
        Returns:
            True se saudável, False caso contrário
        """
        try:
            await self.aembed_text("test")
            logger.info("OpenAI Adapter health check passed (async)")
            return True
        except Exception as e:
            logger.warning(
                "OpenAI Adapter health check failed (async)",
                extra_data={"error": str(e)}
            )
            return False