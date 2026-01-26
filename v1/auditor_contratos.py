"""
Auditor de Contratos com RAG + Agente ReAct
Bootcamp Itaú FIAP 2026 - Aula 2

Sistema de auditoria inteligente de contratos usando:
- RAG (Retrieval-Augmented Generation)
- ChromaDB para armazenamento vetorial
- Agente ReAct do LangChain
- Output estruturado com Pydantic
"""

import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

# Carrega variáveis de ambiente do arquivo .env
load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "❌ OPENAI_API_KEY não encontrada!\n"
        "Por favor, crie um arquivo .env com sua chave:\n"
        "OPENAI_API_KEY=sk-..."
    )


# ============================================================================
# SCHEMA DE SAÍDA ESTRUTURADA
# ============================================================================

class ContractMetadata(BaseModel):
    """
    Schema Pydantic para validar output estruturado do agente.
    Define os metadados que devem ser extraídos de cada contrato.
    """
    garantia_tipo: str = Field(
        description="Tipo de garantia (ex: 'Alienação Fiduciária', 'Fiança', 'Penhor')"
    )
    garantia_objeto: str = Field(
        description="Objeto dado em garantia (ex: 'Imóvel Matrícula 12345')"
    )
    taxa_juros: float = Field(
        description="Taxa de juros mensal em percentual (ex: 1.0 para 1%)"
    )
    prazo_meses: int = Field(
        description="Prazo do contrato em meses"
    )
    valor_principal: float = Field(
        description="Valor principal do contrato em reais"
    )
    risco_legal: str = Field(
        description="Classificação de risco: 'Baixo', 'Médio' ou 'Alto'"
    )
    compliance_check: bool = Field(
        description="True se contrato está em compliance com políticas do banco"
    )


# ============================================================================
# INGESTÃO DE DOCUMENTOS
# ============================================================================

def ingest_contract(
    file_path: str,
    collection_name: str = "contratos",
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> Chroma:
    """
    Carrega documento (PDF ou TXT), divide em chunks e indexa no ChromaDB.
    
    Args:
        file_path: Caminho para o arquivo PDF ou TXT
        collection_name: Nome da coleção no ChromaDB
        chunk_size: Tamanho de cada chunk em caracteres
        chunk_overlap: Quantidade de caracteres sobrepostos entre chunks
        
    Returns:
        Vectorstore ChromaDB indexado
    """
    print(f"📄 Carregando documento: {file_path}")
    
    # 1. Carregar documento (detecta tipo por extensão)
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.txt'):
        loader = TextLoader(file_path, encoding='utf-8')
    else:
        raise ValueError(f"Tipo de arquivo não suportado: {file_path}")
    
    documents = loader.load()
    print(f"   ✓ {len(documents)} página(s) carregada(s)")
    
    # 2. Chunking com RecursiveCharacterTextSplitter
    # Respeita parágrafos, quebras de linha e pontuação
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"   ✓ {len(chunks)} chunks criados")
    
    # 3. Embedding + Indexing no ChromaDB
    print("🔄 Gerando embeddings e indexando no ChromaDB...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory="./chroma_db"
    )
    
    print(f"✅ Indexados {len(chunks)} chunks no ChromaDB (coleção: {collection_name})\n")
    return vectorstore


# ============================================================================
# DEFINIÇÃO DE TOOLS
# ============================================================================

def create_tools(vectorstore: Chroma) -> list:
    """
    Cria lista de tools que o agente pode usar para interagir com o contrato.
    
    Args:
        vectorstore: ChromaDB vectorstore com os chunks indexados
        
    Returns:
        Lista de objetos Tool do LangChain
    """
    
    def search_contract(query: str) -> str:
        """
        Busca chunks relevantes no contrato usando similaridade semântica.
        
        Args:
            query: Pergunta ou palavra-chave sobre o contrato
            
        Returns:
            Chunks encontrados formatados como texto
        """
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        docs = retriever.get_relevant_documents(query)
        
        if not docs:
            return "Nenhum chunk relevante encontrado."
        
        # Formata resultado com separadores
        context = "\n\n---\n\n".join([
            f"Chunk {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(docs)
        ])
        return f"Chunks encontrados:\n\n{context}"
    
    def extract_clause(clause_number: str) -> str:
        """
        Extrai cláusula específica do contrato por número.
        
        Args:
            clause_number: Número da cláusula (ex: '4', '5.1')
            
        Returns:
            Conteúdo da cláusula ou mensagem de erro
        """
        # Formata query para buscar cláusula
        query = f"CLÁUSULA {clause_number.upper()}"
        docs = vectorstore.similarity_search(query, k=1)
        
        if docs:
            return f"Cláusula {clause_number}:\n\n{docs[0].page_content}"
        return f"❌ Cláusula {clause_number} não encontrada."
    
    # Retorna lista de Tools
    return [
        Tool(
            name="search_contract",
            func=search_contract,
            description=(
                "Use this to search for information in the contract. "
                "Input should be a question or keyword (in Portuguese or English). "
                "Example: 'garantias', 'interest rate', 'prazo'"
            )
        ),
        Tool(
            name="extract_clause",
            func=extract_clause,
            description=(
                "Use this to extract a specific clause by number. "
                "Input should be the clause number like '4' or '5.1'. "
                "Example: '4', 'QUINTA'"
            )
        )
    ]


# ============================================================================
# CRIAÇÃO DO AGENTE REACT
# ============================================================================

def create_auditor_agent(vectorstore: Chroma) -> AgentExecutor:
    """
    Cria agente ReAct para auditar contratos automaticamente.
    
    O agente segue o padrão ReAct:
    - Reasoning (Thought): Analisa o que precisa fazer
    - Action: Decide qual tool usar
    - Observation: Observa o resultado da action
    - Repete até ter informação suficiente
    
    Args:
        vectorstore: ChromaDB vectorstore com os chunks indexados
        
    Returns:
        AgentExecutor configurado
    """
    
    # LLM - usando GPT-4 para melhor raciocínio
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0,  # Determinístico para análise legal
        streaming=True
    )
    
    # Tools disponíveis
    tools = create_tools(vectorstore)
    
    # Prompt Template ReAct customizado para auditoria
    prompt_template = """Você é um auditor de contratos especializado do Banco Itaú.
Sua tarefa é analisar contratos bancários e extrair metadados estruturados para avaliação de risco.

Você tem acesso às seguintes ferramentas:

{tools}

Use SEMPRE o seguinte formato:

Thought: [seu raciocínio sobre o que precisa descobrir]
Action: [nome da ferramenta, deve ser uma de: {tool_names}]
Action Input: [entrada para a ferramenta]
Observation: [resultado da ferramenta]
... (repita Thought/Action/Action Input/Observation quantas vezes necessário)
Thought: Agora tenho informação suficiente para responder
Final Answer: [sua resposta estruturada em JSON seguindo o schema ContractMetadata]

IMPORTANTE:
- Sempre busque TODAS as informações necessárias antes de dar a Final Answer
- Use search_contract para encontrar informações sobre: garantias, juros, prazos, valores
- Use extract_clause quando precisar do texto exato de uma cláusula específica
- A Final Answer DEVE ser um JSON válido com os campos:
  * garantia_tipo (string)
  * garantia_objeto (string)
  * taxa_juros (float, apenas o número)
  * prazo_meses (int)
  * valor_principal (float)
  * risco_legal (string: "Baixo", "Médio" ou "Alto")
  * compliance_check (boolean)

Pergunta: {input}

{agent_scratchpad}"""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
    )
    
    # Cria Agent ReAct
    agent = create_react_agent(llm, tools, prompt)
    
    # Cria AgentExecutor (wrapper que gerencia execução)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # Mostra Thought/Action/Observation no console
        max_iterations=10,  # Limite de iterações para evitar loops
        handle_parsing_errors=True,  # Recupera de erros de parsing
        return_intermediate_steps=True  # Retorna histórico de raciocínio
    )
    
    return agent_executor


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """
    Função principal que orquestra todo o fluxo:
    1. Ingestão do contrato
    2. Criação do agente
    3. Execução da análise
    4. Exibição dos resultados
    """
    
    print("=" * 70)
    print("🏦 AUDITOR DE CONTRATOS - BANCO ITAÚ")
    print("=" * 70)
    print()
    
    # 1. INGESTÃO DO CONTRATO
    print("📥 ETAPA 1: Ingestão de Documento\n")
    
    # Tenta carregar PDF primeiro, se não existir usa o TXT de exemplo
    # Usa o diretório do script como base para caminhos relativos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    contract_path = os.path.join(script_dir, "contrato_mutuo.pdf")
    if not os.path.exists(contract_path):
        print(f"⚠️  PDF não encontrado, usando arquivo TXT de exemplo...")
        contract_path = os.path.join(script_dir, "contrato_mutuo_exemplo.txt")
    
    if not os.path.exists(contract_path):
        print(f"❌ Erro: Arquivo {contract_path} não encontrado!")
        print("Por favor, adicione um contrato PDF ou TXT para análise.")
        return
    
    vectorstore = ingest_contract(contract_path)
    
    # 2. CRIAÇÃO DO AGENTE
    print("🤖 ETAPA 2: Criação do Agente ReAct\n")
    agent = create_auditor_agent(vectorstore)
    print("✅ Agente auditor criado e pronto!\n")
    
    # 3. EXECUÇÃO DA ANÁLISE
    print("🔍 ETAPA 3: Análise do Contrato\n")
    print("-" * 70)
    
    query = """
    Analyze this banking contract thoroughly and extract:
    
    1. Type and object of guarantee (garantia_tipo, garantia_objeto)
    2. Interest rate per month (taxa_juros)
    3. Contract term in months (prazo_meses)
    4. Principal amount in reais (valor_principal)
    5. Legal risk assessment: "Baixo", "Médio" or "Alto" (risco_legal)
    6. Compliance status: true or false (compliance_check)
    
    Return ONLY a valid JSON following the ContractMetadata schema.
    """
    
    result = agent.invoke({"input": query})
    
    # 4. EXIBIÇÃO DOS RESULTADOS
    print("\n" + "=" * 70)
    print("✅ RESULTADO FINAL DA AUDITORIA")
    print("=" * 70)
    print()
    print(result["output"])
    print()
    
    # Mostra estatísticas do processo
    if "intermediate_steps" in result:
        steps = result["intermediate_steps"]
        print(f"\n📊 Estatísticas:")
        print(f"   • Iterações do agente: {len(steps)}")
        print(f"   • Tools utilizadas: {[step[0].tool for step in steps]}")
    
    print("\n" + "=" * 70)
    print("🎉 Análise concluída com sucesso!")
    print("=" * 70)


if __name__ == "__main__":
    main()
