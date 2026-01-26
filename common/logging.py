"""
Logging Estruturado
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Sistema de logging estruturado com suporte a JSON e contexto.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from contextvars import ContextVar
from functools import wraps
import time

# Context variable para rastreamento de request/session
request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})


@dataclass
class LogContext:
    """Contexto para logging estruturado."""
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    contract_id: Optional[str] = None
    user_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte contexto para dicionário."""
        result = {}
        if self.request_id:
            result['request_id'] = self.request_id
        if self.session_id:
            result['session_id'] = self.session_id
        if self.contract_id:
            result['contract_id'] = self.contract_id
        if self.user_id:
            result['user_id'] = self.user_id
        result.update(self.extra)
        return result


class JSONFormatter(logging.Formatter):
    """Formatter que produz logs em formato JSON estruturado."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Adiciona contexto do request se disponível
        ctx = request_context.get()
        if ctx:
            log_entry['context'] = ctx
        
        # Adiciona extras do record
        if hasattr(record, 'extra_data') and record.extra_data:
            log_entry['data'] = record.extra_data
        
        # Adiciona exception info se presente
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class PrettyFormatter(logging.Formatter):
    """Formatter que produz logs coloridos e legíveis para desenvolvimento."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Formata mensagem base
        msg = f"{color}[{timestamp}] {record.levelname:8}{self.RESET} | "
        msg += f"{record.name}:{record.funcName}:{record.lineno} | "
        msg += record.getMessage()
        
        # Adiciona extras se presentes
        if hasattr(record, 'extra_data') and record.extra_data:
            msg += f" | {json.dumps(record.extra_data, ensure_ascii=False, default=str)}"
        
        # Adiciona contexto
        ctx = request_context.get()
        if ctx:
            ctx_str = ' '.join(f"{k}={v}" for k, v in ctx.items())
            msg += f" | ctx:[{ctx_str}]"
        
        return msg


class StructuredLogger(logging.Logger):
    """Logger customizado com suporte a dados estruturados."""
    
    def _log_with_extra(
        self,
        level: int,
        msg: str,
        *args,
        extra_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log com dados extras estruturados."""
        extra = kwargs.get('extra', {})
        extra['extra_data'] = extra_data or {}
        kwargs['extra'] = extra
        super()._log(level, msg, args, **kwargs)
    
    def debug(self, msg: str, *args, extra_data: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        self._log_with_extra(logging.DEBUG, msg, *args, extra_data=extra_data, **kwargs)
    
    def info(self, msg: str, *args, extra_data: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        self._log_with_extra(logging.INFO, msg, *args, extra_data=extra_data, **kwargs)
    
    def warning(self, msg: str, *args, extra_data: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        self._log_with_extra(logging.WARNING, msg, *args, extra_data=extra_data, **kwargs)
    
    def error(self, msg: str, *args, extra_data: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        self._log_with_extra(logging.ERROR, msg, *args, extra_data=extra_data, **kwargs)
    
    def critical(self, msg: str, *args, extra_data: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        self._log_with_extra(logging.CRITICAL, msg, *args, extra_data=extra_data, **kwargs)


# Registra a classe customizada
logging.setLoggerClass(StructuredLogger)


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Configura logging global da aplicação.
    
    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Se True, usa formato JSON; caso contrário, formato legível
        log_file: Caminho opcional para arquivo de log
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove handlers existentes
    root_logger.handlers.clear()
    
    # Escolhe formatter
    formatter = JSONFormatter() if json_format else PrettyFormatter()
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Handler para arquivo (opcional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(JSONFormatter())  # Arquivo sempre em JSON
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> StructuredLogger:
    """
    Obtém logger estruturado para um módulo.
    
    Args:
        name: Nome do logger (geralmente __name__)
        
    Returns:
        Logger estruturado configurado
    """
    return logging.getLogger(name)  # type: ignore


def set_context(context: LogContext) -> None:
    """Define contexto para logs subsequentes."""
    request_context.set(context.to_dict())


def clear_context() -> None:
    """Limpa contexto de logging."""
    request_context.set({})


def log_execution_time(logger: Optional[StructuredLogger] = None):
    """
    Decorator para logar tempo de execução de funções.
    
    Args:
        logger: Logger a usar (se None, cria um novo)
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time
                logger.info(
                    f"Function {func.__name__} completed",
                    extra_data={
                        'function': func.__name__,
                        'duration_ms': round(elapsed * 1000, 2),
                        'status': 'success'
                    }
                )
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                logger.error(
                    f"Function {func.__name__} failed",
                    extra_data={
                        'function': func.__name__,
                        'duration_ms': round(elapsed * 1000, 2),
                        'status': 'error',
                        'error': str(e)
                    }
                )
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time
                logger.info(
                    f"Async function {func.__name__} completed",
                    extra_data={
                        'function': func.__name__,
                        'duration_ms': round(elapsed * 1000, 2),
                        'status': 'success'
                    }
                )
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                logger.error(
                    f"Async function {func.__name__} failed",
                    extra_data={
                        'function': func.__name__,
                        'duration_ms': round(elapsed * 1000, 2),
                        'status': 'error',
                        'error': str(e)
                    }
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator
