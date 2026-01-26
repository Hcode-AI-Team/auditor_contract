"""
Testes para Document Loader
Auditor de Contratos - Bootcamp Itaú FIAP 2026
"""

import pytest
from pathlib import Path
from adapters.document_loader import DocumentLoader
from common.exceptions import DocumentLoadError
from common.types import DocumentType


def test_document_loader_initialization():
    """Testa inicialização do document loader."""
    loader = DocumentLoader(chunk_size=500, chunk_overlap=50)
    
    assert loader.chunk_size == 500
    assert loader.chunk_overlap == 50
    assert loader.text_splitter is not None


def test_detect_document_type_pdf():
    """Testa detecção de tipo PDF."""
    loader = DocumentLoader()
    
    doc_type = loader._detect_document_type("test.pdf")
    
    assert doc_type == DocumentType.PDF


def test_detect_document_type_txt():
    """Testa detecção de tipo TXT."""
    loader = DocumentLoader()
    
    doc_type = loader._detect_document_type("test.txt")
    
    assert doc_type == DocumentType.TXT


def test_detect_document_type_unsupported():
    """Testa que erro é levantado para tipo não suportado."""
    loader = DocumentLoader()
    
    with pytest.raises(DocumentLoadError):
        loader._detect_document_type("test.docx")


def test_load_document_file_not_found():
    """Testa que erro é levantado para arquivo inexistente."""
    loader = DocumentLoader()
    
    with pytest.raises(DocumentLoadError):
        loader.load_document("arquivo_inexistente.txt")


def test_load_document_txt_file(tmp_path):
    """Testa carregamento de arquivo TXT."""
    # Cria arquivo temporário
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content\nMultiple lines\n")
    
    loader = DocumentLoader()
    documents = loader.load_document(str(test_file))
    
    assert len(documents) >= 1
    assert "Test content" in documents[0].page_content


def test_split_documents():
    """Testa divisão de documentos em chunks."""
    from langchain.schema import Document
    
    loader = DocumentLoader(chunk_size=50, chunk_overlap=10)
    
    # Cria documento teste
    long_text = "Este é um texto longo que será dividido em múltiplos chunks. " * 10
    documents = [Document(page_content=long_text)]
    
    chunks = loader.split_documents(documents)
    
    assert len(chunks) > 1  # Deve dividir em múltiplos chunks
    assert all(len(chunk.page_content) <= 60 for chunk in chunks)  # Aproximadamente chunk_size
