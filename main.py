"""
Main - Auditor de Contratos
Bootcamp Itaú FIAP 2026

Ponto de entrada principal da aplicação.
"""

import sys
from pathlib import Path

# Configuração
from core.config import Config

# Adapters
from adapters.openai_adapter import OpenAIAdapter
from adapters.chromadb_adapter import ChromaDBAdapter
from adapters.document_loader import DocumentLoader

# Core
from core.agent import AuditorAgent

# Common
from common.exceptions import (
    AuditorError,
    ConfigurationError,
    DocumentLoadError,
    VectorStoreError
)


def print_banner():
    """Exibe banner da aplicação."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║         AUDITOR DE CONTRATOS - BANCO ITAÚ                            ║
║         Bootcamp FIAP 2026 - Aula 2                                  ║
╚══════════════════════════════════════════════════════════════════════╝
    """)


def main():
    """Função principal da aplicação."""
    
    print_banner()
    
    try:
        # ═══════════════════════════════════════════════════════════════
        # 1. CONFIGURAÇÃO
        # ═══════════════════════════════════════════════════════════════
        print("⚙️  ETAPA 1: Carregando Configurações\n")
        
        config = Config.from_env()
        config.validate()
        
        print("✅ Configurações carregadas:")
        print(f"   • LLM: {config.llm_model}")
        print(f"   • Embeddings: {config.embedding_model}")
        print(f"   • Chunk Size: {config.chunk_size}")
        print(f"   • Max Iterations: {config.max_iterations}\n")
        
        # ═══════════════════════════════════════════════════════════════
        # 2. INGESTÃO DE DOCUMENTO
        # ═══════════════════════════════════════════════════════════════
        print("📥 ETAPA 2: Ingestão de Documento\n")
        
        # Define caminho do contrato
        contract_path = "v1/contrato_mutuo_exemplo.txt"
        
        if not Path(contract_path).exists():
            print(f"❌ Erro: Arquivo não encontrado: {contract_path}")
            print("Por favor, adicione um contrato para análise.")
            return 1
        
        # Carrega documento
        document_loader = DocumentLoader(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
        
        chunks = document_loader.process_document(contract_path)
        
        # ═══════════════════════════════════════════════════════════════
        # 3. INICIALIZAÇÃO DE ADAPTERS
        # ═══════════════════════════════════════════════════════════════
        print("🔧 ETAPA 3: Inicializando Adapters\n")
        
        # OpenAI Adapter
        openai_adapter = OpenAIAdapter(
            api_key=config.openai_api_key,
            llm_model=config.llm_model,
            embedding_model=config.embedding_model,
            temperature=config.temperature
        )
        print("   ✓ OpenAI Adapter inicializado")
        
        # ChromaDB Adapter
        chromadb_adapter = ChromaDBAdapter(
            embeddings=openai_adapter.embeddings,
            collection_name=config.collection_name,
            persist_directory=config.persist_directory
        )
        
        # Cria vectorstore com os chunks
        chromadb_adapter.create_from_documents(chunks)
        print("   ✓ ChromaDB Adapter inicializado\n")
        
        # ═══════════════════════════════════════════════════════════════
        # 4. CRIAÇÃO DO AGENTE
        # ═══════════════════════════════════════════════════════════════
        print("🤖 ETAPA 4: Criando Agente ReAct\n")
        
        agent = AuditorAgent(
            openai_adapter=openai_adapter,
            chromadb_adapter=chromadb_adapter,
            max_iterations=config.max_iterations,
            verbose=config.verbose
        )
        
        print("✅ Agente auditor criado e pronto!\n")
        
        # ═══════════════════════════════════════════════════════════════
        # 5. ANÁLISE DO CONTRATO
        # ═══════════════════════════════════════════════════════════════
        print("🔍 ETAPA 5: Análise do Contrato\n")
        
        # Executa análise
        result = agent.analyze_contract()
        
        # ═══════════════════════════════════════════════════════════════
        # 6. EXIBIÇÃO DOS RESULTADOS
        # ═══════════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("✅ RESULTADO FINAL DA AUDITORIA")
        print("=" * 70 + "\n")
        
        # Output JSON
        print("📄 Metadados Extraídos (JSON):")
        print("-" * 70)
        print(result["output"])
        print("-" * 70)
        
        # Tenta parsear e exibir resumo
        try:
            metadata = agent.parse_result_to_schema(result)
            print("\n📊 Resumo do Contrato:")
            print("=" * 70)
            print(metadata.to_summary())
            print("=" * 70)
        except Exception as e:
            print(f"\n⚠️  Não foi possível gerar resumo: {e}")
        
        # Estatísticas
        stats = agent.get_statistics(result)
        print(f"\n📈 Estatísticas da Análise:")
        print(f"   • Iterações do agente: {stats['num_iterations']}")
        print(f"   • Tools utilizadas: {stats['num_tool_calls']} chamadas")
        print(f"   • Tools únicas: {', '.join(stats['unique_tools'])}")
        
        print("\n" + "=" * 70)
        print("🎉 Análise concluída com sucesso!")
        print("=" * 70 + "\n")
        
        return 0
        
    except ConfigurationError as e:
        print(f"\n❌ Erro de Configuração: {e}")
        print("\nVerifique:")
        print("1. Arquivo .env existe na raiz do projeto")
        print("2. OPENAI_API_KEY está definida corretamente")
        return 1
        
    except DocumentLoadError as e:
        print(f"\n❌ Erro ao Carregar Documento: {e}")
        return 1
        
    except VectorStoreError as e:
        print(f"\n❌ Erro no ChromaDB: {e}")
        print("\nDica: Execute 'rm -rf chroma_db' e tente novamente")
        return 1
        
    except AuditorError as e:
        print(f"\n❌ Erro: {e}")
        if e.details:
            print(f"Detalhes: {e.details}")
        return 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Análise interrompida pelo usuário.")
        return 130
        
    except Exception as e:
        print(f"\n❌ Erro Inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
