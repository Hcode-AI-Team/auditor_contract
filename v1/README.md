# 📚 v1 - Versão Didática (Simples)

Esta é a **versão didática** do Auditor de Contratos - tudo em arquivos únicos para facilitar o aprendizado dos conceitos básicos.

## 🎯 Objetivo desta Versão

Esta pasta contém a implementação **simples e direta** do auditor de contratos, ideal para:

- ✅ **Aprender conceitos** de RAG (Retrieval-Augmented Generation)
- ✅ **Entender agentes ReAct** sem complexidade de arquitetura
- ✅ **Testar rapidamente** funcionalidades
- ✅ **Comparar** com a versão refatorada (raiz do projeto)

## 📁 Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `auditor_contratos.py` | **Código principal** - tudo em um arquivo único (~350 linhas) |
| `test_setup.py` | Validação de instalação e configuração |
| `exemplo_uso_avancado.py` | 6 exemplos práticos de uso |
| `utils.py` | Utilitários (limpar ChromaDB, estatísticas, etc) |
| `contrato_mutuo_exemplo.txt` | Contrato de exemplo para testes |

## 🚀 Como Usar

### Instalação

```bash
# Na raiz do projeto (não dentro de v1/)
pip install -r requirements.txt
```

### Configuração

Crie arquivo `.env` na **raiz do projeto**:

```bash
OPENAI_API_KEY=sk-sua-chave-aqui
```

### Execução

```bash
# Executar da raiz do projeto
python v1/auditor_contratos.py
```

## 📖 Estrutura do Código

Todo o código está em `auditor_contratos.py`, organizado da seguinte forma:

```python
# 1. SCHEMA PYDANTIC
class ContractMetadata(BaseModel):
    garantia_tipo: str
    garantia_objeto: str
    # ... 7 campos estruturados

# 2. INGESTÃO DE DOCUMENTOS
def ingest_contract(file_path: str) -> Chroma:
    # PyPDFLoader/TextLoader
    # RecursiveCharacterTextSplitter
    # OpenAI Embeddings
    # ChromaDB indexing

# 3. DEFINIÇÃO DE TOOLS
def create_tools(vectorstore: Chroma) -> list:
    # search_contract(query) -> str
    # extract_clause(number) -> str

# 4. CRIAÇÃO DO AGENTE REACT
def create_auditor_agent(vectorstore: Chroma) -> AgentExecutor:
    # GPT-4 Turbo
    # Prompt template customizado
    # Loop: Thought → Action → Observation

# 5. FUNÇÃO PRINCIPAL
def main():
    # Orquestra todo o fluxo
```

## 🎓 Conceitos Implementados

### RAG (Retrieval-Augmented Generation)
```
PDF → Chunks → Embeddings → ChromaDB
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

### Componentes Principais

- **Chunking**: RecursiveCharacterTextSplitter (500 chars, overlap 50)
- **Embeddings**: OpenAI text-embedding-3-small (1536 dim)
- **Vector DB**: ChromaDB persistente
- **LLM**: GPT-4 Turbo (temperature=0)
- **Tools**: search_contract, extract_clause
- **Output**: JSON validado com Pydantic

## 🔄 Diferença para Versão Refatorada

| Aspecto | v1/ (Simples) | Raiz (Refatorada) |
|---------|---------------|-------------------|
| **Arquitetura** | Arquivo único | Modular (adapters, core, domain) |
| **Complexidade** | Baixa - fácil entender | Alta - padrões profissionais |
| **Testabilidade** | Limitada | Alta (componentes isolados) |
| **Escalabilidade** | Limitada | Alta (fácil adicionar features) |
| **Uso** | Aprendizado e testes | Produção |
| **Linhas de código** | ~350 em 1 arquivo | ~600 em múltiplos arquivos |

## 🎯 Quando Usar v1/

✅ **Use v1/ quando:**
- Aprendendo conceitos de RAG e agentes
- Fazendo testes rápidos
- Prototipando novas ideias
- Ensinando para iniciantes

❌ **Use versão refatorada quando:**
- Colocando em produção
- Trabalhando em equipe
- Adicionando features complexas
- Precisa de testes unitários

## 📚 Próximos Passos

1. **Entenda esta versão primeiro** - rode e experimente
2. **Leia o código** - `auditor_contratos.py` (~350 linhas)
3. **Teste os exemplos** - `python v1/exemplo_uso_avancado.py`
4. **Compare** - veja diferença para versão raiz refatorada
5. **Evolua** - quando precisar de mais estrutura, use versão raiz

## 🐛 Troubleshooting

### Erro: "No module named 'auditor_contratos'"
Execute da raiz do projeto, não de dentro de v1/:
```bash
cd ..  # voltar para raiz
python v1/auditor_contratos.py
```

### Erro: ChromaDB locked
```bash
python v1/utils.py  # opção 1: limpar ChromaDB
```

## 📖 Documentação Completa

Para documentação completa, veja a pasta `docs/` na raiz do projeto:
- `README.md` - Visão geral
- `QUICKSTART.md` - Início rápido
- `INSTALACAO.md` - Instalação detalhada
- `REFERENCIA_RAPIDA.md` - Referência de comandos

---

**💡 Lembre-se**: Esta é a versão didática! Simples e direta para aprender. Para produção, use a versão refatorada na raiz do projeto.

**Bootcamp Itaú FIAP 2026** | Versão Didática
