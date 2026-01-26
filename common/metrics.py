"""
Sistema de Métricas
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Coleta e exposição de métricas para monitoramento.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from collections import defaultdict
from threading import Lock
from functools import wraps
from contextlib import contextmanager
from enum import Enum


class MetricType(str, Enum):
    """Tipos de métricas suportadas."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """Valor de uma métrica com timestamp."""
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class HistogramBuckets:
    """Buckets para histograma."""
    buckets: List[float] = field(default_factory=lambda: [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
    counts: Dict[float, int] = field(default_factory=dict)
    sum: float = 0.0
    count: int = 0
    
    def __post_init__(self):
        self.counts = {b: 0 for b in self.buckets}
        self.counts[float('inf')] = 0
    
    def observe(self, value: float) -> None:
        """Registra um valor no histograma."""
        self.sum += value
        self.count += 1
        for bucket in sorted(self.buckets):
            if value <= bucket:
                self.counts[bucket] += 1
        self.counts[float('inf')] += 1


class MetricsCollector:
    """
    Coletor de métricas singleton.
    
    Suporta:
    - Counters: valores que só incrementam
    - Gauges: valores que podem subir ou descer
    - Histograms: distribuição de valores
    - Timers: duração de operações
    """
    
    _instance: Optional['MetricsCollector'] = None
    _lock: Lock = Lock()
    
    def __new__(cls) -> 'MetricsCollector':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._counters: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._gauges: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._histograms: Dict[str, Dict[str, HistogramBuckets]] = defaultdict(dict)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()
        self._initialized = True
    
    def _labels_key(self, labels: Optional[Dict[str, str]] = None) -> str:
        """Gera chave única para conjunto de labels."""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
    
    # ========================
    # COUNTERS
    # ========================
    
    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Incrementa um counter."""
        key = self._labels_key(labels)
        with self._lock:
            self._counters[name][key] += value
    
    def get_counter(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> float:
        """Obtém valor atual de um counter."""
        key = self._labels_key(labels)
        return self._counters[name][key]
    
    # ========================
    # GAUGES
    # ========================
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Define valor de um gauge."""
        key = self._labels_key(labels)
        with self._lock:
            self._gauges[name][key] = value
    
    def increment_gauge(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Incrementa um gauge."""
        key = self._labels_key(labels)
        with self._lock:
            self._gauges[name][key] += value
    
    def decrement_gauge(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Decrementa um gauge."""
        key = self._labels_key(labels)
        with self._lock:
            self._gauges[name][key] -= value
    
    def get_gauge(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> float:
        """Obtém valor atual de um gauge."""
        key = self._labels_key(labels)
        return self._gauges[name][key]
    
    # ========================
    # HISTOGRAMS
    # ========================
    
    def observe(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        buckets: Optional[List[float]] = None
    ) -> None:
        """Registra observação em um histograma."""
        key = self._labels_key(labels)
        with self._lock:
            if key not in self._histograms[name]:
                self._histograms[name][key] = HistogramBuckets(
                    buckets=buckets or [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
                )
            self._histograms[name][key].observe(value)
    
    def get_histogram(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[HistogramBuckets]:
        """Obtém histograma."""
        key = self._labels_key(labels)
        return self._histograms[name].get(key)
    
    # ========================
    # TIMERS
    # ========================
    
    def record_time(
        self,
        name: str,
        duration_seconds: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Registra tempo de execução."""
        # Usa tanto timer list quanto histogram
        with self._lock:
            self._timers[name].append(duration_seconds)
        self.observe(f"{name}_seconds", duration_seconds, labels)
    
    @contextmanager
    def timer(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager para medir tempo de execução."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.record_time(name, duration, labels)
    
    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """Obtém estatísticas de um timer."""
        times = self._timers.get(name, [])
        if not times:
            return {'count': 0, 'min': 0, 'max': 0, 'avg': 0, 'sum': 0}
        
        return {
            'count': len(times),
            'min': min(times),
            'max': max(times),
            'avg': sum(times) / len(times),
            'sum': sum(times)
        }
    
    # ========================
    # EXPORT
    # ========================
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Exporta todas as métricas em formato estruturado."""
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'counters': {
                name: dict(values) for name, values in self._counters.items()
            },
            'gauges': {
                name: dict(values) for name, values in self._gauges.items()
            },
            'histograms': {
                name: {
                    key: {
                        'buckets': hist.counts,
                        'sum': hist.sum,
                        'count': hist.count
                    }
                    for key, hist in histograms.items()
                }
                for name, histograms in self._histograms.items()
            },
            'timers': {
                name: self.get_timer_stats(name)
                for name in self._timers.keys()
            }
        }
    
    def reset(self) -> None:
        """Reseta todas as métricas."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()


# Instância global
metrics = MetricsCollector()


# ========================
# MÉTRICAS PRÉ-DEFINIDAS
# ========================

class AuditorMetrics:
    """Métricas específicas do Auditor de Contratos."""
    
    # Counters
    CONTRACTS_ANALYZED = "auditor_contracts_analyzed_total"
    CONTRACTS_ERRORS = "auditor_contracts_errors_total"
    TOOL_CALLS = "auditor_tool_calls_total"
    LLM_REQUESTS = "auditor_llm_requests_total"
    EMBEDDINGS_GENERATED = "auditor_embeddings_generated_total"
    CHUNKS_INDEXED = "auditor_chunks_indexed_total"
    VECTOR_SEARCHES = "auditor_vector_searches_total"
    
    # Gauges
    ACTIVE_ANALYSES = "auditor_active_analyses"
    VECTORSTORE_SIZE = "auditor_vectorstore_size"
    
    # Histograms/Timers
    ANALYSIS_DURATION = "auditor_analysis_duration"
    TOOL_DURATION = "auditor_tool_duration"
    LLM_DURATION = "auditor_llm_duration"
    EMBEDDING_DURATION = "auditor_embedding_duration"
    SEARCH_DURATION = "auditor_search_duration"
    
    @staticmethod
    def record_contract_analyzed(success: bool = True, risk_level: str = "unknown") -> None:
        """Registra análise de contrato."""
        if success:
            metrics.increment(
                AuditorMetrics.CONTRACTS_ANALYZED,
                labels={"risk_level": risk_level}
            )
        else:
            metrics.increment(AuditorMetrics.CONTRACTS_ERRORS)
    
    @staticmethod
    def record_tool_call(tool_name: str, duration_seconds: float) -> None:
        """Registra chamada de tool."""
        metrics.increment(
            AuditorMetrics.TOOL_CALLS,
            labels={"tool": tool_name}
        )
        metrics.record_time(
            AuditorMetrics.TOOL_DURATION,
            duration_seconds,
            labels={"tool": tool_name}
        )
    
    @staticmethod
    def record_llm_request(model: str, tokens: int, duration_seconds: float) -> None:
        """Registra requisição ao LLM."""
        metrics.increment(
            AuditorMetrics.LLM_REQUESTS,
            labels={"model": model}
        )
        metrics.record_time(
            AuditorMetrics.LLM_DURATION,
            duration_seconds,
            labels={"model": model}
        )
        # Contador de tokens
        metrics.increment(
            "auditor_llm_tokens_total",
            value=tokens,
            labels={"model": model}
        )
    
    @staticmethod
    def record_embeddings(count: int, duration_seconds: float, model: str) -> None:
        """Registra geração de embeddings."""
        metrics.increment(
            AuditorMetrics.EMBEDDINGS_GENERATED,
            value=count,
            labels={"model": model}
        )
        metrics.record_time(
            AuditorMetrics.EMBEDDING_DURATION,
            duration_seconds,
            labels={"model": model}
        )
    
    @staticmethod
    def record_vector_search(k: int, duration_seconds: float) -> None:
        """Registra busca vetorial."""
        metrics.increment(
            AuditorMetrics.VECTOR_SEARCHES,
            labels={"k": str(k)}
        )
        metrics.record_time(
            AuditorMetrics.SEARCH_DURATION,
            duration_seconds
        )
    
    @staticmethod
    @contextmanager
    def track_analysis():
        """Context manager para rastrear análise em andamento."""
        metrics.increment_gauge(AuditorMetrics.ACTIVE_ANALYSES)
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            metrics.decrement_gauge(AuditorMetrics.ACTIVE_ANALYSES)
            metrics.record_time(AuditorMetrics.ANALYSIS_DURATION, duration)


def track_metrics(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """
    Decorator para rastrear métricas de funções.
    
    Args:
        metric_name: Nome da métrica de tempo
        labels: Labels opcionais
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                metrics.increment(f"{metric_name}_success_total", labels=labels)
                return result
            except Exception:
                metrics.increment(f"{metric_name}_error_total", labels=labels)
                raise
            finally:
                duration = time.perf_counter() - start
                metrics.record_time(metric_name, duration, labels)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                metrics.increment(f"{metric_name}_success_total", labels=labels)
                return result
            except Exception:
                metrics.increment(f"{metric_name}_error_total", labels=labels)
                raise
            finally:
                duration = time.perf_counter() - start
                metrics.record_time(metric_name, duration, labels)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator
