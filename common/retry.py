"""
Retry e Circuit Breaker
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Sistema de retry com backoff exponencial e circuit breaker para resiliência.
"""

import time
import asyncio
from typing import TypeVar, Callable, Any, Optional, Type, Tuple
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from threading import Lock

from common.logging import get_logger
from common.metrics import metrics

logger = get_logger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Estados do circuit breaker."""
    CLOSED = "closed"      # Normal - requisições passam
    OPEN = "open"          # Falhas - requisições bloqueadas
    HALF_OPEN = "half_open"  # Testando - algumas requisições passam


@dataclass
class RetryConfig:
    """Configuração de retry."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    
    def calculate_delay(self, attempt: int) -> float:
        """Calcula delay com backoff exponencial."""
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())
        return delay


@dataclass
class CircuitBreakerConfig:
    """Configuração do circuit breaker."""
    failure_threshold: int = 5          # Falhas para abrir
    success_threshold: int = 3          # Sucessos para fechar
    timeout: float = 30.0               # Tempo em OPEN antes de HALF_OPEN
    half_open_max_calls: int = 3        # Chamadas permitidas em HALF_OPEN


class CircuitBreaker:
    """
    Implementação de Circuit Breaker.
    
    Protege contra falhas em cascata, bloqueando chamadas
    quando um serviço está com problemas.
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0
        self._lock = Lock()
    
    @property
    def state(self) -> CircuitState:
        """Retorna estado atual do circuit."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Verifica se deve ir para HALF_OPEN
                if self._last_failure_time:
                    elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                    if elapsed >= self.config.timeout:
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0
                        logger.info(
                            f"Circuit breaker '{self.name}' transitioning to HALF_OPEN",
                            extra_data={"elapsed_seconds": elapsed}
                        )
            return self._state
    
    def can_execute(self) -> bool:
        """Verifica se pode executar a chamada."""
        state = self.state
        
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.OPEN:
            return False
        else:  # HALF_OPEN
            with self._lock:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
    
    def record_success(self) -> None:
        """Registra sucesso na chamada."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' CLOSED (recovered)")
                    metrics.increment("circuit_breaker_recovered", labels={"name": self.name})
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0
    
    def record_failure(self) -> None:
        """Registra falha na chamada."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                # Qualquer falha em HALF_OPEN volta para OPEN
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(f"Circuit breaker '{self.name}' OPEN (failed in half-open)")
                metrics.increment("circuit_breaker_opened", labels={"name": self.name})
            
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(
                        f"Circuit breaker '{self.name}' OPEN",
                        extra_data={"failure_count": self._failure_count}
                    )
                    metrics.increment("circuit_breaker_opened", labels={"name": self.name})


class CircuitBreakerOpen(Exception):
    """Exceção quando circuit breaker está aberto."""
    pass


# Registry global de circuit breakers
_circuit_breakers: dict[str, CircuitBreaker] = {}
_cb_lock = Lock()


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Obtém ou cria circuit breaker por nome."""
    with _cb_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(name, config)
        return _circuit_breakers[name]


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    circuit_breaker_name: Optional[str] = None
):
    """
    Decorator para retry com backoff exponencial.
    
    Args:
        max_attempts: Número máximo de tentativas
        initial_delay: Delay inicial em segundos
        max_delay: Delay máximo em segundos
        exponential_base: Base para cálculo exponencial
        retry_exceptions: Exceções que devem triggerar retry
        circuit_breaker_name: Nome do circuit breaker (opcional)
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        retry_exceptions=retry_exceptions
    )
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cb = get_circuit_breaker(circuit_breaker_name) if circuit_breaker_name else None
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # Verifica circuit breaker
            if cb and not cb.can_execute():
                raise CircuitBreakerOpen(f"Circuit breaker '{circuit_breaker_name}' is open")
            
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    result = func(*args, **kwargs)
                    if cb:
                        cb.record_success()
                    return result
                    
                except config.retry_exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{config.max_attempts} for {func.__name__}",
                            extra_data={
                                "error": str(e),
                                "delay_seconds": round(delay, 2)
                            }
                        )
                        metrics.increment(
                            "retry_attempts",
                            labels={"function": func.__name__, "attempt": str(attempt + 1)}
                        )
                        time.sleep(delay)
                    else:
                        if cb:
                            cb.record_failure()
                        logger.error(
                            f"All retry attempts exhausted for {func.__name__}",
                            extra_data={"error": str(e)}
                        )
                        metrics.increment("retry_exhausted", labels={"function": func.__name__})
            
            raise last_exception
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            # Verifica circuit breaker
            if cb and not cb.can_execute():
                raise CircuitBreakerOpen(f"Circuit breaker '{circuit_breaker_name}' is open")
            
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    result = await func(*args, **kwargs)
                    if cb:
                        cb.record_success()
                    return result
                    
                except config.retry_exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{config.max_attempts} for {func.__name__} (async)",
                            extra_data={
                                "error": str(e),
                                "delay_seconds": round(delay, 2)
                            }
                        )
                        metrics.increment(
                            "retry_attempts",
                            labels={"function": func.__name__, "attempt": str(attempt + 1)}
                        )
                        await asyncio.sleep(delay)
                    else:
                        if cb:
                            cb.record_failure()
                        logger.error(
                            f"All retry attempts exhausted for {func.__name__} (async)",
                            extra_data={"error": str(e)}
                        )
                        metrics.increment("retry_exhausted", labels={"function": func.__name__})
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Configurações pré-definidas para diferentes cenários
RETRY_CONFIG_OPENAI = {
    "max_attempts": 3,
    "initial_delay": 1.0,
    "max_delay": 30.0,
    "exponential_base": 2.0,
    "circuit_breaker_name": "openai"
}

RETRY_CONFIG_CHROMADB = {
    "max_attempts": 3,
    "initial_delay": 0.5,
    "max_delay": 10.0,
    "exponential_base": 2.0,
    "circuit_breaker_name": "chromadb"
}
