"""
Sistema de Cache
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Cache de embeddings e resultados para reduzir custos de API.
"""

import hashlib
import json
import time
import pickle
from typing import TypeVar, Optional, Dict, Any, List, Callable, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from pathlib import Path
from abc import ABC, abstractmethod
import asyncio

from common.logging import get_logger
from common.metrics import metrics

logger = get_logger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Entrada de cache com metadados."""
    value: T
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    hits: int = 0
    
    def is_expired(self) -> bool:
        """Verifica se entrada expirou."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def record_hit(self) -> None:
        """Registra hit no cache."""
        self.hits += 1


@dataclass
class CacheStats:
    """Estatísticas do cache."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Taxa de acerto do cache."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CacheBackend(ABC):
    """Interface abstrata para backends de cache."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Define valor no cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove valor do cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Limpa todo o cache."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Verifica se chave existe."""
        pass


class InMemoryCache(CacheBackend):
    """
    Cache em memória com suporte a TTL e LRU.
    
    Ideal para desenvolvimento e ambientes single-instance.
    """
    
    def __init__(self, max_size: int = 10000, default_ttl: int = 3600):
        """
        Inicializa cache em memória.
        
        Args:
            max_size: Número máximo de entradas
            default_ttl: TTL padrão em segundos (1 hora)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = Lock()
        self._stats = CacheStats()
        
        logger.info(
            "InMemoryCache initialized",
            extra_data={"max_size": max_size, "default_ttl": default_ttl}
        )
    
    def _generate_expires_at(self, ttl: Optional[int]) -> Optional[datetime]:
        """Gera datetime de expiração."""
        actual_ttl = ttl if ttl is not None else self._default_ttl
        if actual_ttl <= 0:
            return None
        return datetime.utcnow() + timedelta(seconds=actual_ttl)
    
    def _evict_if_needed(self) -> None:
        """Remove entradas antigas se necessário (LRU)."""
        if len(self._cache) >= self._max_size:
            # Remove entrada mais antiga ou com menos hits
            oldest_key = min(
                self._cache.keys(),
                key=lambda k: (self._cache[k].hits, self._cache[k].created_at)
            )
            del self._cache[oldest_key]
            self._stats.evictions += 1
            metrics.increment("cache_evictions")
    
    def _cleanup_expired(self) -> None:
        """Remove entradas expiradas."""
        expired_keys = [
            k for k, v in self._cache.items() if v.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
            self._stats.evictions += 1
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache."""
        with self._lock:
            self._cleanup_expired()
            
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    entry.record_hit()
                    self._stats.hits += 1
                    metrics.increment("cache_hits")
                    return entry.value
                else:
                    del self._cache[key]
            
            self._stats.misses += 1
            metrics.increment("cache_misses")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Define valor no cache."""
        with self._lock:
            self._evict_if_needed()
            
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=self._generate_expires_at(ttl)
            )
            self._stats.size = len(self._cache)
            metrics.set_gauge("cache_size", len(self._cache))
    
    def delete(self, key: str) -> bool:
        """Remove valor do cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.size = len(self._cache)
                return True
            return False
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()
            logger.info("Cache cleared")
    
    def exists(self, key: str) -> bool:
        """Verifica se chave existe."""
        with self._lock:
            if key in self._cache:
                return not self._cache[key].is_expired()
            return False
    
    def get_stats(self) -> CacheStats:
        """Retorna estatísticas do cache."""
        return self._stats


class FileCache(CacheBackend):
    """
    Cache em disco para persistência entre reinícios.
    
    Útil para embeddings que são caros de gerar.
    """
    
    def __init__(self, cache_dir: str = ".cache/embeddings", default_ttl: int = 86400):
        """
        Inicializa cache em disco.
        
        Args:
            cache_dir: Diretório para armazenar cache
            default_ttl: TTL padrão em segundos (24 horas)
        """
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._default_ttl = default_ttl
        self._lock = Lock()
        
        logger.info(
            "FileCache initialized",
            extra_data={"cache_dir": str(self._cache_dir), "default_ttl": default_ttl}
        )
    
    def _get_path(self, key: str) -> Path:
        """Gera caminho do arquivo para a chave."""
        # Usa hash para evitar problemas com caracteres especiais
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self._cache_dir / f"{key_hash}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache."""
        path = self._get_path(key)
        
        if not path.exists():
            metrics.increment("cache_misses")
            return None
        
        try:
            with self._lock:
                with open(path, 'rb') as f:
                    entry: CacheEntry = pickle.load(f)
                
                if entry.is_expired():
                    path.unlink()
                    metrics.increment("cache_misses")
                    return None
                
                metrics.increment("cache_hits")
                return entry.value
                
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Define valor no cache."""
        path = self._get_path(key)
        actual_ttl = ttl if ttl is not None else self._default_ttl
        
        entry = CacheEntry(
            value=value,
            expires_at=datetime.utcnow() + timedelta(seconds=actual_ttl) if actual_ttl > 0 else None
        )
        
        try:
            with self._lock:
                with open(path, 'wb') as f:
                    pickle.dump(entry, f)
        except Exception as e:
            logger.error(f"Error writing cache: {e}")
    
    def delete(self, key: str) -> bool:
        """Remove valor do cache."""
        path = self._get_path(key)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        for path in self._cache_dir.glob("*.cache"):
            path.unlink()
        logger.info("File cache cleared")
    
    def exists(self, key: str) -> bool:
        """Verifica se chave existe."""
        return self._get_path(key).exists()


class EmbeddingCache:
    """
    Cache especializado para embeddings.
    
    Combina cache em memória (rápido) com cache em disco (persistente).
    """
    
    def __init__(
        self,
        memory_cache: Optional[InMemoryCache] = None,
        file_cache: Optional[FileCache] = None,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Inicializa cache de embeddings.
        
        Args:
            memory_cache: Cache em memória (L1)
            file_cache: Cache em disco (L2)
            embedding_model: Modelo de embeddings (para versionamento)
        """
        self._l1_cache = memory_cache or InMemoryCache(max_size=5000, default_ttl=3600)
        self._l2_cache = file_cache or FileCache(default_ttl=86400 * 7)  # 7 dias
        self._model = embedding_model
        
        logger.info(
            "EmbeddingCache initialized",
            extra_data={"model": embedding_model}
        )
    
    def _generate_key(self, text: str) -> str:
        """Gera chave única para o texto."""
        # Inclui modelo para invalidar cache quando modelo muda
        content = f"{self._model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """
        Obtém embedding do cache.
        
        Verifica L1 (memória) primeiro, depois L2 (disco).
        """
        key = self._generate_key(text)
        
        # Tenta L1 (memória)
        result = self._l1_cache.get(key)
        if result is not None:
            logger.debug("Embedding cache L1 hit", extra_data={"text_length": len(text)})
            return result
        
        # Tenta L2 (disco)
        result = self._l2_cache.get(key)
        if result is not None:
            # Promove para L1
            self._l1_cache.set(key, result)
            logger.debug("Embedding cache L2 hit", extra_data={"text_length": len(text)})
            return result
        
        logger.debug("Embedding cache miss", extra_data={"text_length": len(text)})
        return None
    
    def set(self, text: str, embedding: List[float]) -> None:
        """
        Armazena embedding no cache.
        
        Armazena em ambos L1 e L2.
        """
        key = self._generate_key(text)
        
        # Armazena em ambos os níveis
        self._l1_cache.set(key, embedding)
        self._l2_cache.set(key, embedding)
        
        logger.debug("Embedding cached", extra_data={"text_length": len(text)})
    
    def get_many(self, texts: List[str]) -> Dict[str, Optional[List[float]]]:
        """Obtém múltiplos embeddings do cache."""
        return {text: self.get(text) for text in texts}
    
    def set_many(self, embeddings: Dict[str, List[float]]) -> None:
        """Armazena múltiplos embeddings no cache."""
        for text, embedding in embeddings.items():
            self.set(text, embedding)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        l1_stats = self._l1_cache.get_stats()
        return {
            "l1_hits": l1_stats.hits,
            "l1_misses": l1_stats.misses,
            "l1_size": l1_stats.size,
            "l1_hit_rate": l1_stats.hit_rate,
            "model": self._model
        }
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        self._l1_cache.clear()
        self._l2_cache.clear()


# Instância global do cache de embeddings
_embedding_cache: Optional[EmbeddingCache] = None


def get_embedding_cache(model: str = "text-embedding-3-small") -> EmbeddingCache:
    """Obtém instância global do cache de embeddings."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache(embedding_model=model)
    return _embedding_cache


def cached_embedding(cache: Optional[EmbeddingCache] = None):
    """
    Decorator para cachear embeddings.
    
    Args:
        cache: Instância do cache (usa global se None)
    """
    def decorator(func: Callable) -> Callable:
        nonlocal cache
        
        @wraps(func)
        def sync_wrapper(self, text: str) -> List[float]:
            c = cache or get_embedding_cache()
            
            # Tenta cache
            cached = c.get(text)
            if cached is not None:
                return cached
            
            # Gera embedding
            result = func(self, text)
            
            # Armazena no cache
            c.set(text, result)
            
            return result
        
        @wraps(func)
        async def async_wrapper(self, text: str) -> List[float]:
            c = cache or get_embedding_cache()
            
            # Tenta cache
            cached = c.get(text)
            if cached is not None:
                return cached
            
            # Gera embedding
            result = await func(self, text)
            
            # Armazena no cache
            c.set(text, result)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
