# 📚 Referência Rápida - Auditor de Contratos

Guia de referência para os principais comandos e conceitos.

## 🚀 Comandos Essenciais

### Setup Inicial
```bash
# 1. Criar ambiente virtual
python -m venv venv

# 2. Ativar (Windows)
venv\Scripts\activate

# 2. Ativar (Linux/Mac)
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar API Key
echo "OPENAI_API_KEY=sk-sua-chave" > .env
```

### Executar Aplicações
```bash
# Teste de configuração
python test_setup.py

# Análise de contrato (principal)
python auditor_contratos.py

# Exemplos avançados
python exemplo_uso_avancado.py

# Utilitários
python utils.py
```

### Utilitários Rápidos
```python
# Limpar banco vetorial
from utils import limpar_chromadb
limpar_chromadb()

# Ver estatísticas
from utils import estatisticas_projeto
estatisticas_projeto()

# Listar collections
from utils import listar_collections
listar_collections()
```

## 📦 Estrutura de Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `auditor_contratos.py` | **Código principal** - Sistema completo de auditoria |
| `test_setup.py` | Testa instalação e configuração |
| `exemplo_uso_avancado.py` | Exemplos de uso programático |
| `utils.py` | Funções utilitárias auxiliares |
| `contrato_mutuo_exemplo.txt` | Contrato de exemplo para testes |
| `requirements.txt` | Dependências do projeto |
| `README.md` | Documentação completa |
| `QUICKSTART.md` | Guia de início rápido |

## 🧩 Componentes Principais

### 1. Schema Pydantic

```python
from auditor_contratos import ContractMetadata

metadata = ContractMetadata(
    garantia_tipo="Alienação Fiduciária",
    garantia_objeto="Imóvel Matrícula 12345",
    taxa_juros=1.0,
    prazo_meses=36,
    valor_principal=1500000.0,
    risco_legal="Baixo",
    compliance_check=True
)
```

### 2. Ingestão de Documentos

```python
from auditor_contratos import ingest_contract

# PDF ou TXT
vectorstore = ingest_contract(
    "contrato.pdf",
    collection_name="contratos",
    chunk_size=500,
    chunk_overlap=50
)
```

### 3. Criação do Agente

```python
from auditor_contratos import create_auditor_agent

agent = create_auditor_agent(vectorstore)

result = agent.invoke({
    "input": "Extract contract metadata as JSON"
})

print(result["output"])
```

### 4. Busca Direta (Sem Agente)

```python
# Busca por similaridade
docs = vectorstore.similarity_search("garantias", k=3)

# Busca com score
results = vectorstore.similarity_search_with_score("juros", k=3)
for doc, score in results:
    print(f"Score: {score:.4f}")
    print(doc.page_content)
```

## 🔧 Parâmetros Configuráveis

### Chunking
```python
chunk_size=500        # Tamanho do chunk em caracteres
chunk_overlap=50      # Sobreposição entre chunks
```

**Diretrizes:**
- **Pequeno (200-300)**: Melhor precisão, mais chunks
- **Médio (500-800)**: Balanceado (recomendado)
- **Grande (1000+)**: Mais contexto, menos precisão

### LLM
```python
model="gpt-4-turbo-preview"  # Melhor raciocínio
model="gpt-3.5-turbo"         # Mais barato e rápido
temperature=0                 # Determinístico
```

### Embedding
```python
model="text-embedding-3-small"   # 1536 dim, rápido
model="text-embedding-3-large"   # 3072 dim, preciso
```

### Retrieval
```python
search_kwargs={"k": 3}   # Top 3 chunks
search_kwargs={"k": 5}   # Top 5 chunks
```

## 🎯 Queries Úteis

### Análise Completa
```python
query = "Extract all metadata as JSON following ContractMetadata schema."
```

### Análise de Compliance
```python
query = """
Check compliance with:
1. Interest rate < 2% per month
2. Real estate guarantee required
3. Minimum 12 months term

Return ContractMetadata JSON with risk_legal classification.
"""
```

### Busca Específica
```python
query = "What are the penalties for late payment?"
query = "What is the total contract value?"
query = "Describe all guarantees provided."
```

## 🐛 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| `ModuleNotFoundError` | Ativar venv: `venv\Scripts\activate` |
| `OPENAI_API_KEY not found` | Criar arquivo `.env` com a chave |
| Agente em loop infinito | Reduzir `max_iterations` ou melhorar prompt |
| Poucos chunks retornados | Aumentar `k` em `search_kwargs` |
| ChromaDB locked | Fechar outros processos e deletar `chroma_db/` |
| JSON inválido no output | Usar `handle_parsing_errors=True` no AgentExecutor |

## 💰 Estimativa de Custos (OpenAI)

### Por Contrato (~2 páginas, 5 iterações)

| Componente | Tokens | Custo |
|------------|--------|-------|
| Embeddings (small) | ~1,500 | $0.0002 |
| GPT-4 Turbo | ~3,000 | $0.09 |
| **TOTAL** | | **~$0.10** |

### Otimizações de Custo

1. **Use GPT-3.5-turbo**: ~$0.01 por contrato (10x mais barato)
2. **Cache embeddings**: Não reprocessar contratos já indexados
3. **Reduza iterações**: `max_iterations=3` em vez de 10
4. **Chunks maiores**: Menos chunks = menos embeddings

## 📊 Métricas de Performance

### Tempos Típicos

| Operação | Tempo | Otimização |
|----------|-------|------------|
| Ingestão (1 PDF, 5 pgs) | ~5s | Cache vectorstore |
| Embedding generation | ~2s | Batch processing |
| Agent execution (5 iter) | ~15s | Reduzir iterações |
| **TOTAL** | **~20s** | |

### ChromaDB Storage

- **1 contrato (5 pgs)**: ~50 KB
- **100 contratos**: ~5 MB
- **1000 contratos**: ~50 MB

## 🎓 Conceitos-Chave

### RAG (Retrieval-Augmented Generation)
Combina busca semântica com geração de texto:
1. **Retrieve**: Buscar chunks relevantes no vectorstore
2. **Augment**: Adicionar contexto ao prompt
3. **Generate**: LLM gera resposta baseada no contexto

### ReAct (Reasoning + Acting)
Padrão de agente que alterna entre raciocínio e ação:
1. **Thought**: "Preciso buscar informações sobre X"
2. **Action**: `search_contract("X")`
3. **Observation**: Resultado da action
4. Repete até ter informação suficiente
5. **Final Answer**: Resposta estruturada

### Embeddings Vetoriais
Representação numérica de texto que captura significado semântico:
```
"garantia" → [0.12, -0.45, 0.89, ...]  (1536 dimensões)
"guarantee" → [0.15, -0.43, 0.91, ...] (similar!)
```

### Chunking
Divisão de documentos em pedaços menores para busca eficiente:
- **Character-based**: Corta a cada N caracteres
- **Recursive**: Respeita estrutura (parágrafos, frases)
- **Semantic**: Agrupa frases com mesmo tópico

## 🔗 Links Úteis

- [LangChain Docs](https://python.langchain.com/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [ReAct Paper (arXiv)](https://arxiv.org/abs/2210.03629)

## 📞 Suporte

Para dúvidas sobre o material didático, consulte o arquivo `index.html` no navegador.

---

**Última atualização**: Janeiro 2026 | Bootcamp Itaú FIAP
