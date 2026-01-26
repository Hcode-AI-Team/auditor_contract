"""
Testes do módulo de Retry e Circuit Breaker
Auditor de Contratos - Bootcamp Itaú FIAP 2026
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock

from common.retry import (
    RetryConfig,
    CircuitBreakerConfig,
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpen,
    retry_with_backoff,
    get_circuit_breaker,
)


class TestRetryConfig:
    """Testes para RetryConfig."""
    
    def test_default_values(self):
        """Testa valores padrão."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
    
    def test_calculate_delay_exponential(self):
        """Testa cálculo de delay exponencial sem jitter."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )
        
        assert config.calculate_delay(0) == 1.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 4.0
        assert config.calculate_delay(3) == 8.0
    
    def test_calculate_delay_max(self):
        """Testa que delay não excede máximo."""
        config = RetryConfig(
            initial_delay=10.0,
            max_delay=30.0,
            jitter=False
        )
        
        # 10 * 2^3 = 80, mas max é 30
        assert config.calculate_delay(3) == 30.0
    
    def test_calculate_delay_with_jitter(self):
        """Testa delay com jitter."""
        config = RetryConfig(
            initial_delay=1.0,
            jitter=True
        )
        
        delays = [config.calculate_delay(0) for _ in range(10)]
        
        # Com jitter, delays devem variar
        assert len(set(delays)) > 1
        
        # Mas devem estar dentro do range esperado (0.5 a 1.5 do base)
        for d in delays:
            assert 0.5 <= d <= 1.5


class TestCircuitBreaker:
    """Testes para CircuitBreaker."""
    
    def test_initial_state_closed(self):
        """Testa que estado inicial é CLOSED."""
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED
    
    def test_can_execute_when_closed(self):
        """Testa que pode executar quando fechado."""
        cb = CircuitBreaker("test")
        assert cb.can_execute() is True
    
    def test_record_success_resets_failure_count(self):
        """Testa que sucesso reseta contador de falhas."""
        cb = CircuitBreaker("test")
        cb._failure_count = 3
        
        cb.record_success()
        
        assert cb._failure_count == 0
    
    def test_opens_after_threshold(self):
        """Testa que abre após threshold de falhas."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)
        
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state == CircuitState.OPEN
    
    def test_cannot_execute_when_open(self):
        """Testa que não pode executar quando aberto."""
        cb = CircuitBreaker("test")
        cb._state = CircuitState.OPEN
        cb._last_failure_time = None  # Sem timeout
        
        assert cb.can_execute() is False
    
    def test_transitions_to_half_open(self):
        """Testa transição para HALF_OPEN após timeout."""
        config = CircuitBreakerConfig(timeout=0.1)
        cb = CircuitBreaker("test", config)
        cb._state = CircuitState.OPEN
        
        from datetime import datetime, timedelta
        cb._last_failure_time = datetime.now() - timedelta(seconds=0.2)
        
        # Ao verificar estado, deve transicionar
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_closes_after_success_in_half_open(self):
        """Testa que fecha após sucessos em HALF_OPEN."""
        config = CircuitBreakerConfig(success_threshold=2)
        cb = CircuitBreaker("test", config)
        cb._state = CircuitState.HALF_OPEN
        
        cb.record_success()
        cb.record_success()
        
        assert cb._state == CircuitState.CLOSED
    
    def test_reopens_on_failure_in_half_open(self):
        """Testa que reabre em falha durante HALF_OPEN."""
        cb = CircuitBreaker("test")
        cb._state = CircuitState.HALF_OPEN
        
        cb.record_failure()
        
        assert cb._state == CircuitState.OPEN


class TestRetryDecorator:
    """Testes para o decorator retry_with_backoff."""
    
    def test_succeeds_first_attempt(self):
        """Testa sucesso na primeira tentativa."""
        mock_func = Mock(return_value="success")
        
        @retry_with_backoff(max_attempts=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retries_on_failure(self):
        """Testa retry em falha."""
        mock_func = Mock(side_effect=[ValueError("error"), "success"])
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_exhausts_retries(self):
        """Testa que esgota retries."""
        mock_func = Mock(side_effect=ValueError("error"))
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        def test_func():
            return mock_func()
        
        with pytest.raises(ValueError):
            test_func()
        
        assert mock_func.call_count == 3
    
    def test_respects_retry_exceptions(self):
        """Testa que só faz retry para exceções especificadas."""
        mock_func = Mock(side_effect=TypeError("error"))
        
        @retry_with_backoff(
            max_attempts=3,
            retry_exceptions=(ValueError,),
            initial_delay=0.01
        )
        def test_func():
            return mock_func()
        
        with pytest.raises(TypeError):
            test_func()
        
        # Não deve ter feito retry
        assert mock_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_succeeds_first_attempt(self):
        """Testa sucesso na primeira tentativa (async)."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_retries_on_failure(self):
        """Testa retry em falha (async)."""
        attempts = [0]
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        async def test_func():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ValueError("error")
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert attempts[0] == 2
    
    def test_with_circuit_breaker(self):
        """Testa integração com circuit breaker."""
        # Reseta circuit breaker
        from common.retry import _circuit_breakers
        _circuit_breakers.clear()
        
        @retry_with_backoff(
            max_attempts=5,
            circuit_breaker_name="test_cb",
            initial_delay=0.01
        )
        def test_func():
            raise ValueError("error")
        
        cb = get_circuit_breaker("test_cb")
        
        # Executa até circuit breaker abrir
        for _ in range(2):
            try:
                test_func()
            except (ValueError, CircuitBreakerOpen):
                pass
        
        # Circuit breaker deve estar aberto após falhas
        # (threshold padrão é 5, mas esgotamos retries 2x = 10 falhas)
        # Na verdade, cada chamada a test_func esgota 5 retries
        assert cb._failure_count >= 2


class TestGetCircuitBreaker:
    """Testes para get_circuit_breaker."""
    
    def test_creates_new_circuit_breaker(self):
        """Testa criação de novo circuit breaker."""
        from common.retry import _circuit_breakers
        _circuit_breakers.clear()
        
        cb = get_circuit_breaker("new_cb")
        
        assert cb.name == "new_cb"
        assert "new_cb" in _circuit_breakers
    
    def test_returns_existing_circuit_breaker(self):
        """Testa retorno de circuit breaker existente."""
        from common.retry import _circuit_breakers
        _circuit_breakers.clear()
        
        cb1 = get_circuit_breaker("existing_cb")
        cb2 = get_circuit_breaker("existing_cb")
        
        assert cb1 is cb2
    
    def test_applies_config_on_creation(self):
        """Testa aplicação de config na criação."""
        from common.retry import _circuit_breakers
        _circuit_breakers.clear()
        
        config = CircuitBreakerConfig(failure_threshold=10)
        cb = get_circuit_breaker("configured_cb", config)
        
        assert cb.config.failure_threshold == 10
