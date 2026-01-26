# 🏦 Auditor de Contratos - RAG + Agente ReAct

Sistema inteligente de auditoria de contratos bancários usando RAG (Retrieval-Augmented Generation) com ChromaDB e Agente ReAct do LangChain.

**Bootcamp Itaú FIAP 2026 - Aula 2**

---

## 🎯 Funcionalidades

- ✅ **Ingestão automática** de contratos (PDF ou TXT)
- ✅ **Chunking inteligente** com RecursiveCharacterTextSplitter
- ✅ **Embeddings vetoriais** com OpenAI text-embedding-3-small
- ✅ **Busca semântica** no ChromaDB
- ✅ **Agente ReAct** com raciocínio passo a passo
- ✅ **Output estruturado** validado com Pydantic
- ✅ **Extração de metadados** de risco e compliance

## 🏗️ Arquitetura

```
PDF/TXT → PyPDFLoader → RecursiveTextSplitter → OpenAI Embeddings
                                                         ↓
    User Query → ReAct Agent → Tools → ChromaDB Vector Search
                      ↓
                 JSON Output (ContractMetadata)
```

## 📋 Pré-requisitos

- **Python 3.9+**
- **Chave API da OpenAI** ([obtenha aqui](https://platform.openai.com/api-keys))
- ~100MB de espaço em disco para o ChromaDB

## 🚀 Instalação

### 1. Clone o repositório (ou navegue até a pasta)

```bash
cd aula2
```

### 2. Crie um ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure a API Key da OpenAI

Crie um arquivo `.env` na raiz do projeto:

```bash
OPENAI_API_KEY=sk-sua-chave-aqui
```

## 💻 Uso

### Execução Básica

```bash
python auditor_contratos.py
```

O sistema irá:
1. Carregar o contrato (`contrato_mutuo.pdf` ou `contrato_mutuo_exemplo.txt`)
2. Dividir em chunks e gerar embeddings
3. Indexar no ChromaDB
4. Criar o agente ReAct
5. Analisar o contrato e extrair metadados
6. Exibir resultado em JSON

### Exemplo de Output

```json
{
  "garantia_tipo": "Alienação Fiduciária",
  "garantia_objeto": "Imóvel Matrícula 12345 do 2º CRI São Paulo",
  "taxa_juros": 1.0,
  "prazo_meses": 36,
  "valor_principal": 1500000.0,
  "risco_legal": "Baixo",
  "compliance_check": true
}
```

## 📦 Estrutura do Projeto

```
aula2/
├── auditor_contratos.py          # Código principal
├── requirements.txt               # Dependências
├── contrato_mutuo_exemplo.txt    # Contrato de exemplo
├── index.html                     # Material didático
├── README.md                      # Este arquivo
└── chroma_db/                     # Banco vetorial (gerado)
```

## 🛠️ Componentes Principais

### 1. Schema Pydantic (`ContractMetadata`)

Define a estrutura dos metadados extraídos:
- `garantia_tipo`: Tipo de garantia
- `garantia_objeto`: Objeto dado em garantia
- `taxa_juros`: Taxa mensal (%)
- `prazo_meses`: Prazo em meses
- `valor_principal`: Valor em reais
- `risco_legal`: "Baixo", "Médio" ou "Alto"
- `compliance_check`: Booleano

### 2. Ingestão (`ingest_contract()`)

- Carrega PDF ou TXT
- Divide em chunks de 500 caracteres (overlap 50)
- Gera embeddings com OpenAI
- Indexa no ChromaDB

### 3. Tools (`create_tools()`)

**`search_contract`**: Busca semântica por palavras-chave
```python
query = "garantias"
# Retorna top-3 chunks mais relevantes
```

**`extract_clause`**: Extrai cláusula por número
```python
clause_number = "4"
# Retorna texto da CLÁUSULA QUARTA
```

### 4. Agente ReAct (`create_auditor_agent()`)

Segue o padrão **Reasoning + Acting**:
```
Thought: Preciso buscar informações sobre garantias
Action: search_contract
Action Input: "garantias"
Observation: [resultado da busca]
...
Thought: Agora tenho informação suficiente
Final Answer: {...json...}
```

## 🧪 Exercícios Avançados

O material didático (`index.html`) contém exercícios extras:

### 🟢 Básico
- ✅ Setup do ambiente
- ✅ Ingestão de documento
- Testar diferentes `chunk_sizes` (256, 512, 1024)

### 🔵 Intermediário
- Criar tool customizada de cálculo financeiro
- Validação avançada com Pydantic
- Adicionar campos extras ao schema

### 🟠 Avançado
- **Hybrid Search**: Combinar BM25 + embeddings
- **Memory**: ConversationBufferMemory para múltiplas perguntas
- **Multi-Document RAG**: Indexar vários contratos

### 🔴 Expert
- **Plan-and-Execute Agent**: Substituir ReAct por planejamento complexo
- Comparar custos e latência entre abordagens

## 🐛 Troubleshooting

### Erro: "OPENAI_API_KEY não encontrada"
Certifique-se de criar o arquivo `.env` com a chave válida.

### Erro: "No module named 'langchain'"
Ative o ambiente virtual e rode `pip install -r requirements.txt`.

### ChromaDB retorna poucos resultados
Ajuste o parâmetro `k` em `search_kwargs={"k": 3}` para buscar mais chunks.

### Agente entra em loop infinito
- Reduza `max_iterations` no `AgentExecutor`
- Melhore as descrições das tools
- Use modelo mais avançado (GPT-4)

## 📚 Recursos Adicionais

- [LangChain Docs](https://python.langchain.com/docs/get_started/introduction)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)

## 📝 Licença

Este projeto é material didático do Bootcamp Itaú FIAP 2026.

## 👥 Autores

Material desenvolvido para o Bootcamp de IA - Itaú & FIAP

---

**💡 Dica**: Explore o arquivo `index.html` no navegador para ver todo o material teórico sobre RAG, chunking, embeddings, vector databases e agentes!
