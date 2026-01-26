"""
Script de teste para verificar instalação e configuração
Bootcamp Itaú FIAP 2026 - Aula 2
"""

import sys
import os

def test_python_version():
    """Verifica versão do Python"""
    print("🐍 Testando versão do Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (requer 3.9+)")
        return False

def test_imports():
    """Verifica se todas as dependências estão instaladas"""
    print("\n📦 Testando imports...")
    
    dependencies = [
        ("dotenv", "python-dotenv"),
        ("langchain", "langchain"),
        ("langchain_openai", "langchain-openai"),
        ("langchain_community", "langchain-community"),
        ("chromadb", "chromadb"),
        ("pydantic", "pydantic"),
        ("pypdf", "pypdf"),
    ]
    
    all_ok = True
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name} - Execute: pip install {package_name}")
            all_ok = False
    
    return all_ok

def test_env_file():
    """Verifica se o arquivo .env existe e contém a chave"""
    print("\n🔑 Testando configuração API Key...")
    
    if not os.path.exists(".env"):
        print("   ❌ Arquivo .env não encontrado")
        print("      Crie um arquivo .env com: OPENAI_API_KEY=sk-...")
        return False
    
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("   ❌ OPENAI_API_KEY não definida no .env")
        return False
    
    if not api_key.startswith("sk-"):
        print("   ⚠️  API Key não parece válida (deve começar com 'sk-')")
        return False
    
    print(f"   ✅ OPENAI_API_KEY configurada ({api_key[:8]}...)")
    return True

def test_openai_connection():
    """Testa conexão com a API da OpenAI"""
    print("\n🌐 Testando conexão com OpenAI...")
    
    try:
        from dotenv import load_dotenv
        from langchain_openai import OpenAIEmbeddings
        
        load_dotenv()
        
        # Tenta criar um embedding simples
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        result = embeddings.embed_query("teste")
        
        if len(result) > 0:
            print(f"   ✅ Conexão OK (embedding dimension: {len(result)})")
            return True
        else:
            print("   ❌ Resposta vazia da API")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro ao conectar: {str(e)}")
        return False

def test_contract_file():
    """Verifica se há um contrato para processar"""
    print("\n📄 Testando arquivo de contrato...")
    
    files = ["contrato_mutuo.pdf", "contrato_mutuo_exemplo.txt"]
    
    for file in files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} encontrado ({size} bytes)")
            return True
    
    print("   ⚠️  Nenhum contrato encontrado (contrato_mutuo.pdf ou contrato_mutuo_exemplo.txt)")
    print("      O sistema criará um arquivo de exemplo na primeira execução.")
    return True  # Não é erro crítico

def main():
    """Executa todos os testes"""
    print("=" * 70)
    print("🏦 AUDITOR DE CONTRATOS - Teste de Setup")
    print("=" * 70)
    
    results = [
        test_python_version(),
        test_imports(),
        test_env_file(),
        test_contract_file(),
    ]
    
    print("\n" + "=" * 70)
    
    if all(results):
        print("✅ TODOS OS TESTES PASSARAM!")
        print("\nVocê está pronto para executar:")
        print("   python auditor_contratos.py")
        
        # Teste opcional de conexão (pode ser lento)
        print("\n" + "=" * 70)
        response = input("\n🌐 Deseja testar a conexão com OpenAI? (s/N): ")
        if response.lower() in ['s', 'sim', 'y', 'yes']:
            test_openai_connection()
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("\nCorreja os problemas acima antes de executar o auditor.")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
