# 🏦 Auditor de Contratos - RAG + Agente ReAct

Sistema inteligente de auditoria de contratos bancários usando RAG (Retrieval-Augmented Generation) com ChromaDB e Agente ReAct do LangChain.

**Bootcamp Itaú FIAP 2026 - Aula 2**

---

## 🎯 Duas Versões Disponíveis

Este projeto oferece **duas implementações** para fins didáticos:

### 📁 v1/ - Versão Simples (Didática)
**Para aprender conceitos básicos**
- Tudo em arquivo único (`v1/auditor_contratos.py`)
- ~350 linhas de código fáceis de entender
- Ideal para iniciantes em RAG e agentes

```bash
python v1/auditor_contratos.py
```

[📖 Ver documentação da v1](v1/README.md)

### 📁 Raiz - Versão Profissional (Refatorada)
**Para produção e projetos reais**
- Arquitetura modular (adapters, core, domain)
- Separação de responsabilidades
- Padrões de design profissionais
- Testes unitários

```bash
python main.py
```

---

## 🏗️ Arquitetura (Versão Profissional)

```
auditor-contratos/
├── v1/                      # Versão didática simples
├── adapters/                # Integrações externas
│   ├── openai_adapter.py
│   ├── chromadb_adapter.py
│   └── document_loader.py
├── common/                  # Código compartilhado
│   ├── exceptions.py
│   └── types.py
├── core/                    # Lógica principal
│   ├── agent.py
│   └── config.py
├── domain/                  # Modelos de domínio
│   ├── contract_schema.py
│   └── tools.py
├── prompts/                 # Templates de prompts
│   └── system_prompt.txt
├── tests/                   # Testes unitários
├── tutorial/                # (para preencher depois)
├── docs/                    # Documentação
└── main.py                  # Ponto de entrada
```

## 🚀 Quickstart

### 1. Instalação

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Ativar (Linux/Mac)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configuração

Crie arquivo `.env` na raiz:

```bash
OPENAI_API_KEY=sk-sua-chave-aqui
```

### 3. Execução

**Versão Simples (v1):**
```bash
python v1/auditor_contratos.py
```

**Versão Profissional:**
```bash
python main.py
```

## 📊 Funcionalidades

- ✅ **Ingestão automática** de contratos (PDF ou TXT)
- ✅ **Chunking inteligente** com RecursiveCharacterTextSplitter
- ✅ **Embeddings vetoriais** com OpenAI
- ✅ **Busca semântica** no ChromaDB
- ✅ **Agente ReAct** com raciocínio passo a passo
- ✅ **Output estruturado** validado com Pydantic
- ✅ **Extração de 7 metadados** estruturados

## 🎓 Conceitos Implementados

### RAG (Retrieval-Augmented Generation)
```
Documento → Chunks → Embeddings → ChromaDB
                                      ↓
Query → Busca Semântica → Contexto → LLM → Resposta
```

### Agente ReAct (Reasoning + Acting)
```
Thought: "Preciso buscar garantias"
Action: search_contract
Action Input: "garantias"
Observation: [chunks encontrados]
... (repete até ter informação suficiente)
Final Answer: {JSON estruturado}
```

## 📦 Componentes Principais

### Versão Profissional

#### Adapters Layer
- **OpenAIAdapter**: Cliente para LLM e Embeddings
- **ChromaDBAdapter**: Cliente para Vector Store
- **DocumentLoader**: Carregamento de PDFs/TXT

#### Domain Layer
- **ContractMetadata**: Schema Pydantic com 7 campos
- **Tools**: `search_contract`, `extract_clause`

#### Core Layer
- **AuditorAgent**: Agente ReAct completo
- **Config**: Sistema de configuração centralizado

## 🧪 Testes

```bash
# Executar testes
pytest tests/

# Com cobertura
pytest tests/ --cov=.

# Teste específico
pytest tests/test_config.py
```

## 📚 Documentação Completa

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Início rápido em 5 minutos
- **[INSTALACAO.md](docs/INSTALACAO.md)** - Guia detalhado de instalação
- **[REFERENCIA_RAPIDA.md](docs/REFERENCIA_RAPIDA.md)** - Referência de comandos
- **[PROJETO_COMPLETO.md](docs/PROJETO_COMPLETO.md)** - Visão geral do projeto

## 🔄 Comparação: v1 vs Versão Profissional

| Aspecto | v1 (Simples) | Raiz (Profissional) |
|---------|--------------|---------------------|
| **Arquitetura** | Arquivo único | Modular (7 pastas) |
| **Linhas de código** | ~350 em 1 arquivo | ~1500 em múltiplos arquivos |
| **Complexidade** | Baixa | Alta |
| **Testabilidade** | Limitada | Alta (testes unitários) |
| **Escalabilidade** | Limitada | Alta |
| **Manutenibilidade** | Difícil | Fácil |
| **Uso recomendado** | Aprendizado | Produção |

## 💡 Quando Usar Cada Versão

### Use v1/ quando:
- 📚 Aprendendo conceitos de RAG e agentes
- 🧪 Fazendo testes rápidos
- 🎨 Prototipando novas ideias
- 👨‍🏫 Ensinando para iniciantes

### Use versão profissional quando:
- 🏭 Colocando em produção
- 👥 Trabalhando em equipe
- 🚀 Adicionando features complexas
- 🧪 Precisa de testes unitários

## 🐛 Troubleshooting

### Erro: "OPENAI_API_KEY não encontrada"
Crie arquivo `.env` na raiz com sua chave API.

### Erro: ChromaDB locked
```bash
rm -rf chroma_db
python main.py
```

### Erro: ModuleNotFoundError
Ative o ambiente virtual e instale dependências:
```bash
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

## 📖 Material Didático

Abra `index.html` no navegador para ver o material teórico completo sobre:
- Fundamentos de RAG
- Estratégias de chunking
- Embedding models
- Vector databases
- Agentes ReAct
- Exercícios práticos

## 🎯 Próximos Passos

1. ✅ Execute a versão simples (v1) para entender conceitos
2. ✅ Leia o código de `v1/auditor_contratos.py`
3. ✅ Execute a versão profissional (`python main.py`)
4. ✅ Compare as duas implementações
5. ✅ Explore o material teórico em `index.html`
6. ✅ Implemente os exercícios avançados

## 📄 Licença

Material didático do Bootcamp Itaú FIAP 2026.

## 👥 Autores

Bootcamp de IA - Itaú & FIAP

---

**💡 Dica**: Comece pela versão simples (v1/) para aprender, depois evolua para a versão profissional!
