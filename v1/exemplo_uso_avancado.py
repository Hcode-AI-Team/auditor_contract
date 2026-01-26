"""
Exemplo de Uso Avançado do Auditor de Contratos
Mostra como usar o código programaticamente e customizar comportamento
"""

import os
from dotenv import load_dotenv
from auditor_contratos import (
    ingest_contract,
    create_auditor_agent,
    ContractMetadata
)
import json

# Carrega variáveis de ambiente
load_dotenv()


def exemplo_basico():
    """
    Exemplo 1: Uso básico - análise de um contrato
    """
    print("=" * 70)
    print("EXEMPLO 1: Análise Básica")
    print("=" * 70)
    
    # Ingestão
    vectorstore = ingest_contract("contrato_mutuo_exemplo.txt")
    
    # Criar agente
    agent = create_auditor_agent(vectorstore)
    
    # Query simples
    result = agent.invoke({
        "input": "Extract all contract metadata as JSON following ContractMetadata schema."
    })
    
    print("\n📊 Resultado:")
    print(result["output"])


def exemplo_query_customizada():
    """
    Exemplo 2: Query customizada para análise específica
    """
    print("\n" + "=" * 70)
    print("EXEMPLO 2: Query Customizada")
    print("=" * 70)
    
    vectorstore = ingest_contract("contrato_mutuo_exemplo.txt")
    agent = create_auditor_agent(vectorstore)
    
    # Query focada em compliance
    query = """
    Analyze this contract for compliance issues:
    
    1. Check if interest rate is above 2% per month (HIGH RISK)
    2. Check if guarantee is real estate (PREFERRED)
    3. Check if term is longer than 24 months (ACCEPTABLE)
    4. Verify if there's a penalty clause for late payment
    
    Return ContractMetadata JSON with appropriate risk_legal classification:
    - "Baixo" if all checks pass
    - "Médio" if 1-2 issues
    - "Alto" if 3+ issues
    """
    
    result = agent.invoke({"input": query})
    
    print("\n📊 Resultado da Análise de Compliance:")
    print(result["output"])


def exemplo_multiplos_contratos():
    """
    Exemplo 3: Processar múltiplos contratos
    """
    print("\n" + "=" * 70)
    print("EXEMPLO 3: Múltiplos Contratos")
    print("=" * 70)
    
    # Lista de contratos para processar
    contratos = [
        "contrato_mutuo_exemplo.txt",
        # "contrato_002.pdf",
        # "contrato_003.pdf",
    ]
    
    resultados = []
    
    for i, contrato_path in enumerate(contratos):
        if not os.path.exists(contrato_path):
            print(f"⚠️  Arquivo não encontrado: {contrato_path}")
            continue
        
        print(f"\n📄 Processando contrato {i+1}/{len(contratos)}: {contrato_path}")
        
        # Usar collection_name único para cada contrato
        vectorstore = ingest_contract(
            contrato_path,
            collection_name=f"contrato_{i+1}"
        )
        
        agent = create_auditor_agent(vectorstore)
        
        result = agent.invoke({
            "input": "Extract all metadata as JSON following ContractMetadata schema."
        })
        
        resultados.append({
            "contrato": contrato_path,
            "metadata": result["output"]
        })
    
    print("\n" + "=" * 70)
    print("📊 RESUMO DE TODOS OS CONTRATOS")
    print("=" * 70)
    
    for res in resultados:
        print(f"\n📄 {res['contrato']}:")
        print(res['metadata'])


def exemplo_com_validacao_pydantic():
    """
    Exemplo 4: Validar output com Pydantic
    """
    print("\n" + "=" * 70)
    print("EXEMPLO 4: Validação com Pydantic")
    print("=" * 70)
    
    vectorstore = ingest_contract("contrato_mutuo_exemplo.txt")
    agent = create_auditor_agent(vectorstore)
    
    result = agent.invoke({
        "input": "Extract metadata as JSON following ContractMetadata schema."
    })
    
    # Tentar parsear como JSON e validar com Pydantic
    try:
        # Extrair JSON do resultado (pode vir com texto adicional)
        output_text = result["output"]
        
        # Procurar por JSON no texto
        import re
        json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            
            # Validar com Pydantic
            metadata = ContractMetadata(**data)
            
            print("\n✅ Validação Pydantic bem-sucedida!")
            print("\n📊 Dados validados:")
            print(f"   • Garantia: {metadata.garantia_tipo}")
            print(f"   • Taxa de Juros: {metadata.taxa_juros}% ao mês")
            print(f"   • Prazo: {metadata.prazo_meses} meses")
            print(f"   • Valor: R$ {metadata.valor_principal:,.2f}")
            print(f"   • Risco: {metadata.risco_legal}")
            print(f"   • Compliance: {'✅ OK' if metadata.compliance_check else '❌ Não conforme'}")
            
            # Calcular montante final (juros compostos)
            montante = metadata.valor_principal * ((1 + metadata.taxa_juros/100) ** metadata.prazo_meses)
            juros_total = montante - metadata.valor_principal
            
            print(f"\n💰 Cálculo Financeiro:")
            print(f"   • Montante Final: R$ {montante:,.2f}")
            print(f"   • Juros Totais: R$ {juros_total:,.2f}")
            
        else:
            print("❌ Não foi possível extrair JSON do resultado")
            print(f"Output recebido: {output_text}")
            
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao parsear JSON: {e}")
    except Exception as e:
        print(f"❌ Erro na validação: {e}")


def exemplo_busca_direta():
    """
    Exemplo 5: Busca direta no vectorstore (sem agente)
    """
    print("\n" + "=" * 70)
    print("EXEMPLO 5: Busca Direta (Sem Agente)")
    print("=" * 70)
    
    vectorstore = ingest_contract("contrato_mutuo_exemplo.txt")
    
    # Buscar chunks relacionados a "garantias"
    print("\n🔍 Buscando: 'garantias'")
    docs = vectorstore.similarity_search("garantias", k=2)
    
    for i, doc in enumerate(docs):
        print(f"\n📄 Chunk {i+1}:")
        print(doc.page_content)
        print(f"   Metadata: {doc.metadata}")
    
    # Buscar com score
    print("\n" + "-" * 70)
    print("🔍 Buscando com similarity score: 'taxa de juros'")
    results = vectorstore.similarity_search_with_score("taxa de juros", k=2)
    
    for i, (doc, score) in enumerate(results):
        print(f"\n📄 Chunk {i+1} (score: {score:.4f}):")
        print(doc.page_content)


def exemplo_configuracoes_customizadas():
    """
    Exemplo 6: Configurações customizadas de chunking
    """
    print("\n" + "=" * 70)
    print("EXEMPLO 6: Configurações Customizadas")
    print("=" * 70)
    
    # Testar diferentes tamanhos de chunk
    configs = [
        {"chunk_size": 200, "chunk_overlap": 20},
        {"chunk_size": 500, "chunk_overlap": 50},
        {"chunk_size": 1000, "chunk_overlap": 100},
    ]
    
    for config in configs:
        print(f"\n🔧 Testando: chunk_size={config['chunk_size']}, overlap={config['chunk_overlap']}")
        
        vectorstore = ingest_contract(
            "contrato_mutuo_exemplo.txt",
            collection_name=f"test_{config['chunk_size']}",
            **config
        )
        
        # Estatísticas
        print(f"   Collection criada com sucesso")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║         EXEMPLOS DE USO AVANÇADO - AUDITOR DE CONTRATOS             ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Menu interativo
    print("Escolha um exemplo para executar:\n")
    print("1. Análise Básica")
    print("2. Query Customizada (Compliance)")
    print("3. Múltiplos Contratos")
    print("4. Validação com Pydantic")
    print("5. Busca Direta (Sem Agente)")
    print("6. Configurações Customizadas")
    print("0. Executar TODOS os exemplos")
    
    choice = input("\nDigite o número do exemplo (ou Enter para sair): ").strip()
    
    if choice == "1":
        exemplo_basico()
    elif choice == "2":
        exemplo_query_customizada()
    elif choice == "3":
        exemplo_multiplos_contratos()
    elif choice == "4":
        exemplo_com_validacao_pydantic()
    elif choice == "5":
        exemplo_busca_direta()
    elif choice == "6":
        exemplo_configuracoes_customizadas()
    elif choice == "0":
        exemplo_basico()
        exemplo_query_customizada()
        exemplo_multiplos_contratos()
        exemplo_com_validacao_pydantic()
        exemplo_busca_direta()
        exemplo_configuracoes_customizadas()
    else:
        print("Saindo...")
    
    print("\n" + "=" * 70)
    print("✅ Exemplos concluídos!")
    print("=" * 70)
