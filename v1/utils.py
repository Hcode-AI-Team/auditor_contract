"""
Utilitários para o Auditor de Contratos
Funções auxiliares para tarefas comuns
"""

import os
import shutil
from pathlib import Path


def limpar_chromadb():
    """
    Remove o diretório do ChromaDB para começar do zero
    """
    db_path = Path("./chroma_db")
    
    if db_path.exists():
        try:
            shutil.rmtree(db_path)
            print("✅ ChromaDB limpo com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Erro ao limpar ChromaDB: {e}")
            return False
    else:
        print("ℹ️  ChromaDB já está vazio")
        return True


def listar_collections():
    """
    Lista todas as collections no ChromaDB
    """
    try:
        import chromadb
        
        client = chromadb.PersistentClient(path="./chroma_db")
        collections = client.list_collections()
        
        if collections:
            print(f"\n📊 Collections encontradas ({len(collections)}):\n")
            for coll in collections:
                # Tentar pegar contagem de documentos
                try:
                    count = coll.count()
                    print(f"   • {coll.name}: {count} documentos")
                except:
                    print(f"   • {coll.name}")
        else:
            print("ℹ️  Nenhuma collection encontrada")
        
        return collections
        
    except Exception as e:
        print(f"❌ Erro ao listar collections: {e}")
        return []


def estatisticas_projeto():
    """
    Mostra estatísticas do projeto
    """
    print("\n" + "=" * 70)
    print("📊 ESTATÍSTICAS DO PROJETO")
    print("=" * 70 + "\n")
    
    # Contar arquivos Python
    py_files = list(Path(".").glob("*.py"))
    print(f"📄 Arquivos Python: {len(py_files)}")
    for f in py_files:
        lines = len(f.read_text(encoding='utf-8').splitlines())
        print(f"   • {f.name}: {lines} linhas")
    
    # Contar arquivos de documentação
    doc_files = list(Path(".").glob("*.md"))
    print(f"\n📝 Arquivos Markdown: {len(doc_files)}")
    for f in doc_files:
        print(f"   • {f.name}")
    
    # Verificar ChromaDB
    if Path("./chroma_db").exists():
        size = sum(f.stat().st_size for f in Path("./chroma_db").rglob('*') if f.is_file())
        print(f"\n💾 ChromaDB: {size / 1024:.2f} KB")
    else:
        print(f"\n💾 ChromaDB: não criado ainda")
    
    # Verificar .env
    if Path(".env").exists():
        print("\n🔑 Configuração: .env encontrado ✅")
    else:
        print("\n🔑 Configuração: .env NÃO encontrado ❌")
    
    # Verificar contratos
    contratos = list(Path(".").glob("*.pdf")) + list(Path(".").glob("contrato*.txt"))
    print(f"\n📄 Contratos disponíveis: {len(contratos)}")
    for c in contratos:
        size = c.stat().st_size / 1024
        print(f"   • {c.name} ({size:.2f} KB)")


def criar_contrato_teste():
    """
    Cria um contrato de teste mais complexo
    """
    contrato = """CONTRATO DE FINANCIAMENTO EMPRESARIAL
BANCO ITAÚ S.A. - CONTRATO Nº 2024-00123

PARTES:
CREDOR: Banco Itaú Unibanco S.A., inscrito no CNPJ 60.701.190/0001-04
DEVEDOR: Tech Solutions LTDA, inscrita no CNPJ 12.345.678/0001-90

CLÁUSULA PRIMEIRA - DO OBJETO E FINALIDADE
1.1. O CREDOR concede ao DEVEDOR um financiamento no valor de R$ 2.500.000,00 (dois milhões e quinhentos mil reais).
1.2. Os recursos serão destinados exclusivamente à aquisição de equipamentos e expansão da infraestrutura tecnológica.
1.3. O DEVEDOR compromete-se a utilizar os recursos conforme plano de negócios aprovado.

CLÁUSULA SEGUNDA - DAS CONDIÇÕES FINANCEIRAS
2.1. Taxa de Juros: 1.5% (um e meio por cento) ao mês, correspondente a aproximadamente 19.56% ao ano.
2.2. IOF: De acordo com a legislação vigente.
2.3. Correção Monetária: IPCA acumulado anualmente.
2.4. Forma de Pagamento: Sistema de Amortização Constante (SAC).

CLÁUSULA TERCEIRA - DO PRAZO E PAGAMENTO
3.1. Prazo Total: 48 (quarenta e oito) meses.
3.2. Carência: 6 (seis) meses para início do pagamento das parcelas.
3.3. Parcelas: 42 parcelas mensais consecutivas.
3.4. Vencimento: Todo dia 15 de cada mês.

CLÁUSULA QUARTA - DAS GARANTIAS
4.1. O DEVEDOR oferece as seguintes garantias:
    a) Alienação fiduciária do imóvel comercial situado na Av. Paulista, 1000, São Paulo/SP, matrícula 45.678 do 1º CRI.
    b) Fiança dos sócios João Silva (CPF 123.456.789-00) e Maria Santos (CPF 987.654.321-00).
    c) Penhor de 50% das ações da empresa Tech Solutions LTDA.

CLÁUSULA QUINTA - DO INADIMPLEMENTO E PENALIDADES
5.1. Atraso de até 10 dias: Multa de 2% sobre o valor da parcela.
5.2. Atraso superior a 10 dias: Multa de 10% sobre o valor da parcela + juros de mora de 1% ao mês.
5.3. Inadimplência por mais de 90 dias: Vencimento antecipado de todas as parcelas.
5.4. Cobrança: Todas as despesas de cobrança serão de responsabilidade do DEVEDOR.

CLÁUSULA SEXTA - DO VENCIMENTO ANTECIPADO
6.1. O CREDOR poderá declarar vencidas todas as obrigações nas seguintes hipóteses:
    a) Inadimplência superior a 90 dias;
    b) Falência ou recuperação judicial do DEVEDOR;
    c) Alienação das garantias sem autorização prévia;
    d) Descumprimento de qualquer cláusula contratual.

CLÁUSULA SÉTIMA - DAS DISPOSIÇÕES GERAIS
7.1. Foro: Comarca de São Paulo/SP.
7.2. Alterações: Somente por escrito e de comum acordo.
7.3. Notificações: Serão enviadas ao endereço cadastrado.

Data: 15 de janeiro de 2024

_______________________________
Banco Itaú Unibanco S.A.
Representante Legal

_______________________________
Tech Solutions LTDA
Representante Legal
"""
    
    filename = "contrato_teste_complexo.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(contrato)
    
    print(f"✅ Contrato de teste criado: {filename}")
    return filename


def menu_principal():
    """
    Menu interativo de utilitários
    """
    while True:
        print("\n" + "=" * 70)
        print("🛠️  UTILITÁRIOS - AUDITOR DE CONTRATOS")
        print("=" * 70)
        print("\n1. Limpar ChromaDB")
        print("2. Listar Collections")
        print("3. Estatísticas do Projeto")
        print("4. Criar Contrato de Teste")
        print("0. Sair")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == "1":
            limpar_chromadb()
        elif choice == "2":
            listar_collections()
        elif choice == "3":
            estatisticas_projeto()
        elif choice == "4":
            criar_contrato_teste()
        elif choice == "0":
            print("\n👋 Até logo!")
            break
        else:
            print("\n❌ Opção inválida!")


if __name__ == "__main__":
    menu_principal()
