"""
Testes do módulo de Cache
Auditor de Contratos - Bootcamp Itaú FIAP 2026
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from common.cache import (
    CacheEntry,
    CacheStats,
    InMemoryCache,
    FileCache,
    EmbeddingCache,
    get_embedding_cache,
)


class TestCacheEntry:
    """Testes para CacheEntry."""
    
    def test_not_expired_without_expiry(self):
        """Testa que entrada sem expiração nunca expira."""
        entry = CacheEntry(value="test", expires_at=None)
        assert entry.is_expired() is False
    
    def test_not_expired_before_time(self):
        """Testa que entrada não expira antes do tempo."""
        entry = CacheEntry(
            value="test",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        assert entry.is_expired() is False
    
    def test_expired_after_time(self):
        """Testa que entrada expira após o tempo."""
        entry = CacheEntry(
            value="test",
            expires_at=datetime.utcnow() - timedelta(seconds=1)
        )
        assert entry.is_expired() is True
    
    def test_record_hit(self):
        """Testa contagem de hits."""
        entry = CacheEntry(value="test")
        assert entry.hits == 0
        
        entry.record_hit()
        assert entry.hits == 1
        
        entry.record_hit()
        assert entry.hits == 2


class TestCacheStats:
    """Testes para CacheStats."""
    
    def test_hit_rate_zero_when_empty(self):
        """Testa que hit rate é 0 quando vazio."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0
    
    def test_hit_rate_calculation(self):
        """Testa cálculo de hit rate."""
        stats = CacheStats(hits=7, misses=3)
        assert stats.hit_rate == 0.7


class TestInMemoryCache:
    """Testes para InMemoryCache."""
    
    def test_set_and_get(self):
        """Testa set e get básico."""
        cache = InMemoryCache()
        
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"
    
    def test_get_nonexistent_returns_none(self):
        """Testa que get de chave inexistente retorna None."""
        cache = InMemoryCache()
        
        assert cache.get("nonexistent") is None
    
    def test_ttl_expiration(self):
        """Testa expiração por TTL."""
        cache = InMemoryCache(default_ttl=1)
        
        cache.set("key1", "value1", ttl=0)  # TTL 0 = sem expiração
        cache.set("key2", "value2", ttl=1)  # TTL 1 segundo
        
        # Espera expirar
        time.sleep(1.1)
        
        assert cache.get("key1") == "value1"  # Não expira
        assert cache.get("key2") is None  # Expirou
    
    def test_eviction_on_max_size(self):
        """Testa eviction quando atinge tamanho máximo."""
        cache = InMemoryCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Deve evictar key1
        
        assert cache.get("key4") == "value4"
        # Uma das primeiras chaves deve ter sido evictada
        values = [cache.get("key1"), cache.get("key2"), cache.get("key3")]
        assert values.count(None) >= 1
    
    def test_delete(self):
        """Testa delete."""
        cache = InMemoryCache()
        
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("key1") is False
    
    def test_clear(self):
        """Testa clear."""
        cache = InMemoryCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_exists(self):
        """Testa exists."""
        cache = InMemoryCache()
        
        cache.set("key1", "value1")
        
        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False
    
    def test_stats_tracking(self):
        """Testa tracking de estatísticas."""
        cache = InMemoryCache()
        
        cache.set("key1", "value1")
        
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss
        
        stats = cache.get_stats()
        assert stats.hits == 2
        assert stats.misses == 1


class TestFileCache:
    """Testes para FileCache."""
    
    @pytest.fixture
    def temp_dir(self):
        """Cria diretório temporário para testes."""
        path = tempfile.mkdtemp()
        yield path
        shutil.rmtree(path)
    
    def test_set_and_get(self, temp_dir):
        """Testa set e get básico."""
        cache = FileCache(cache_dir=temp_dir)
        
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"
    
    def test_get_nonexistent_returns_none(self, temp_dir):
        """Testa que get de chave inexistente retorna None."""
        cache = FileCache(cache_dir=temp_dir)
        
        assert cache.get("nonexistent") is None
    
    def test_persistence(self, temp_dir):
        """Testa persistência entre instâncias."""
        cache1 = FileCache(cache_dir=temp_dir)
        cache1.set("key1", "value1")
        
        # Nova instância
        cache2 = FileCache(cache_dir=temp_dir)
        
        assert cache2.get("key1") == "value1"
    
    def test_delete(self, temp_dir):
        """Testa delete."""
        cache = FileCache(cache_dir=temp_dir)
        
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
    
    def test_clear(self, temp_dir):
        """Testa clear."""
        cache = FileCache(cache_dir=temp_dir)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_exists(self, temp_dir):
        """Testa exists."""
        cache = FileCache(cache_dir=temp_dir)
        
        cache.set("key1", "value1")
        
        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False
    
    def test_complex_values(self, temp_dir):
        """Testa armazenamento de valores complexos."""
        cache = FileCache(cache_dir=temp_dir)
        
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        cache.set("embedding1", embedding)
        
        assert cache.get("embedding1") == embedding


class TestEmbeddingCache:
    """Testes para EmbeddingCache."""
    
    @pytest.fixture
    def temp_dir(self):
        """Cria diretório temporário para testes."""
        path = tempfile.mkdtemp()
        yield path
        shutil.rmtree(path)
    
    def test_set_and_get(self, temp_dir):
        """Testa set e get básico."""
        memory = InMemoryCache()
        file = FileCache(cache_dir=temp_dir)
        cache = EmbeddingCache(memory_cache=memory, file_cache=file)
        
        embedding = [0.1, 0.2, 0.3]
        cache.set("text1", embedding)
        
        assert cache.get("text1") == embedding
    
    def test_l1_hit(self, temp_dir):
        """Testa hit no cache L1 (memória)."""
        memory = InMemoryCache()
        file = FileCache(cache_dir=temp_dir)
        cache = EmbeddingCache(memory_cache=memory, file_cache=file)
        
        embedding = [0.1, 0.2, 0.3]
        cache.set("text1", embedding)
        
        # Limpa L2 para forçar L1 hit
        file.clear()
        
        assert cache.get("text1") == embedding
    
    def test_l2_hit_promotes_to_l1(self, temp_dir):
        """Testa hit no L2 promove para L1."""
        memory = InMemoryCache()
        file = FileCache(cache_dir=temp_dir)
        cache = EmbeddingCache(memory_cache=memory, file_cache=file)
        
        embedding = [0.1, 0.2, 0.3]
        
        # Armazena só no L2
        key = cache._generate_key("text1")
        file.set(key, embedding)
        
        # Busca deve promover para L1
        result = cache.get("text1")
        
        assert result == embedding
        assert memory.get(key) == embedding
    
    def test_miss(self, temp_dir):
        """Testa cache miss."""
        memory = InMemoryCache()
        file = FileCache(cache_dir=temp_dir)
        cache = EmbeddingCache(memory_cache=memory, file_cache=file)
        
        assert cache.get("nonexistent") is None
    
    def test_get_many(self, temp_dir):
        """Testa get_many."""
        memory = InMemoryCache()
        file = FileCache(cache_dir=temp_dir)
        cache = EmbeddingCache(memory_cache=memory, file_cache=file)
        
        cache.set("text1", [0.1])
        cache.set("text2", [0.2])
        
        results = cache.get_many(["text1", "text2", "text3"])
        
        assert results["text1"] == [0.1]
        assert results["text2"] == [0.2]
        assert results["text3"] is None
    
    def test_set_many(self, temp_dir):
        """Testa set_many."""
        memory = InMemoryCache()
        file = FileCache(cache_dir=temp_dir)
        cache = EmbeddingCache(memory_cache=memory, file_cache=file)
        
        cache.set_many({
            "text1": [0.1],
            "text2": [0.2]
        })
        
        assert cache.get("text1") == [0.1]
        assert cache.get("text2") == [0.2]
    
    def test_model_versioning(self, temp_dir):
        """Testa que modelo diferente gera chave diferente."""
        memory = InMemoryCache()
        file = FileCache(cache_dir=temp_dir)
        
        cache1 = EmbeddingCache(memory_cache=memory, file_cache=file, embedding_model="model-v1")
        cache2 = EmbeddingCache(memory_cache=memory, file_cache=file, embedding_model="model-v2")
        
        key1 = cache1._generate_key("same text")
        key2 = cache2._generate_key("same text")
        
        assert key1 != key2
    
    def test_stats(self, temp_dir):
        """Testa estatísticas."""
        memory = InMemoryCache()
        file = FileCache(cache_dir=temp_dir)
        cache = EmbeddingCache(memory_cache=memory, file_cache=file)
        
        cache.set("text1", [0.1])
        cache.get("text1")  # Hit
        cache.get("text2")  # Miss
        
        stats = cache.get_stats()
        assert "l1_hits" in stats
        assert "l1_misses" in stats
    
    def test_clear(self, temp_dir):
        """Testa clear."""
        memory = InMemoryCache()
        file = FileCache(cache_dir=temp_dir)
        cache = EmbeddingCache(memory_cache=memory, file_cache=file)
        
        cache.set("text1", [0.1])
        cache.clear()
        
        assert cache.get("text1") is None


class TestGetEmbeddingCache:
    """Testes para get_embedding_cache."""
    
    def test_returns_singleton(self):
        """Testa que retorna singleton."""
        from common.cache import _embedding_cache
        
        # Reseta
        import common.cache
        common.cache._embedding_cache = None
        
        cache1 = get_embedding_cache()
        cache2 = get_embedding_cache()
        
        assert cache1 is cache2
