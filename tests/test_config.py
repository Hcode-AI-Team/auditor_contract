"""
Testes para Core Config
Auditor de Contratos - Bootcamp Itaú FIAP 2026
"""

import os
import pytest
from core.config import Config
from common.exceptions import ConfigurationError


def test_config_from_env_with_api_key(monkeypatch):
    """Testa criação de config com API key válida."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
    
    config = Config.from_env()
    
    assert config.openai_api_key == "sk-test123"
    assert config.llm_model is not None
    assert config.chunk_size > 0


def test_config_from_env_without_api_key(monkeypatch):
    """Testa que ConfigurationError é levantada sem API key."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    with pytest.raises(ConfigurationError):
        Config.from_env()


def test_config_validation_invalid_api_key():
    """Testa validação de API key inválida."""
    config = Config(openai_api_key="invalid-key")
    
    with pytest.raises(ConfigurationError):
        config.validate()


def test_config_validation_invalid_chunk_size():
    """Testa validação de chunk size inválido."""
    config = Config(
        openai_api_key="sk-test123",
        chunk_size=50  # Muito pequeno
    )
    
    with pytest.raises(ConfigurationError):
        config.validate()


def test_config_validation_chunk_overlap_too_large():
    """Testa validação de overlap maior que size."""
    config = Config(
        openai_api_key="sk-test123",
        chunk_size=100,
        chunk_overlap=150  # Maior que size
    )
    
    with pytest.raises(ConfigurationError):
        config.validate()


def test_config_str_hides_full_api_key():
    """Testa que __str__ não expõe API key completa."""
    config = Config(openai_api_key="sk-test123456789")
    
    config_str = str(config)
    
    assert "sk-test123" in config_str
    assert "sk-test123456789" not in config_str
