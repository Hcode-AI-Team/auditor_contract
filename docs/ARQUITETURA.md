# 🏗️ Arquitetura do Auditor de Contratos

Documentação detalhada da arquitetura da versão profissional.

---

## Visão Geral

O Auditor de Contratos segue uma **arquitetura em camadas** com separação clara de responsabilidades, inspirada em Domain-Driven Design (DDD) e Clean Architecture.

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                   │
│                      main.py                            │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                     Core Layer                          │
│            agent.py  │  config.py                       │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
┌────────▼────┐  ┌────▼─────┐  ┌───▼──────┐
│   Domain    │  │ Adapters │  │  Common  │
│   Layer     │  │  Layer   │  │  Layer   │
└─────────────┘  └──────────┘  └──────────┘
```

---

## Camadas da Aplicação

### 1. Presentation Layer (main.py)

**Responsabilidade**: Ponto de entrada da aplicação.

- Orquestra o fluxo completo
- Exibe informações ao usuário
- Trata erros e exceções
- Não contém lógica de negócio

```python
def main():
    config = Config.from_env()
    adapters = create_adapters(config)
    agent = AuditorAgent(adapters)
    result = agent.analyze_contract()
```

### 2. Core Layer

**Responsabilidade**: Lógica principal da aplicação.

#### core/agent.py
- Implementa o Agente ReAct
- Gerencia loop Thought/Action/Observation
- Coordena uso de tools
- Parseia resultados

#### core/config.py
- Carrega configurações do `.env`
- Valida configurações
- Fornece valores padrão
- Centraliza constantes

### 3. Domain Layer

**Responsabilidade**: Modelos de domínio e regras de negócio.

#### domain/contract_schema.py
- Define `ContractMetadata` (Pydantic)
- Validadores de negócio
- Cálculos financeiros
- Formatação de outputs

#### domain/tools.py
- Define tools do agente
- Implementa lógica das tools
- Encapsula acesso ao vectorstore

### 4. Adapters Layer

**Responsabilidade**: Integrações com sistemas externos.

#### adapters/openai_adapter.py
- Cliente para OpenAI API
- Gerencia LLM e Embeddings
- Lazy loading de recursos

#### adapters/chromadb_adapter.py
- Cliente para ChromaDB
- Operações de busca vetorial
- Gerenciamento de coleções

#### adapters/document_loader.py
- Carrega PDFs e TXT
- Divide documentos em chunks
- Processa múltiplos arquivos

### 5. Common Layer

**Responsabilidade**: Código compartilhado.

#### common/exceptions.py
- Hierarquia de exceções
- Mensagens de erro padronizadas

#### common/types.py
- Enums (DocumentType, ChunkingStrategy, RiskLevel)
- Constantes da aplicação
- Protocols (interfaces)

---

## Fluxo de Dados

### Ingestão de Documento

```
PDF/TXT File
    │
    ▼
DocumentLoader.load_document()
    │
    ▼
RecursiveCharacterTextSplitter
    │
    ▼
List[Document] (chunks)
    │
    ▼
OpenAIAdapter.embeddings.embed_documents()
    │
    ▼
ChromaDBAdapter.create_from_documents()
    │
    ▼
ChromaDB (persisted)
```

### Análise de Contrato (ReAct Loop)

```
User Query
    │
    ▼
AuditorAgent.analyze_contract()
    │
    ▼
┌──────────────────────────────────┐
│      ReAct Loop                  │
│  ┌────────────────────────────┐  │
│  │ 1. Thought                 │  │
│  │    LLM reasons about task  │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │ 2. Action                  │  │
│  │    Choose tool to use      │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │ 3. Action Input            │  │
│  │    Prepare tool input      │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │ 4. Execute Tool            │  │
│  │    - search_contract()     │  │
│  │    - extract_clause()      │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │ 5. Observation             │  │
│  │    Tool result             │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  └───────────►│ Repeat until     │
│               │ have enough info  │
└───────────────┼───────────────────┘
                │
    ┌───────────▼───────────────┐
    │ 6. Final Answer           │
    │    ContractMetadata JSON  │
    └───────────┬───────────────┘
                │
                ▼
    Pydantic Validation
                │
                ▼
    ContractMetadata Object
```

---

## Padrões de Design Aplicados

### 1. Dependency Injection

Componentes recebem dependências via construtor:

```python
class AuditorAgent:
    def __init__(
        self,
        openai_adapter: OpenAIAdapter,
        chromadb_adapter: ChromaDBAdapter
    ):
        self.openai_adapter = openai_adapter
        self.chromadb_adapter = chromadb_adapter
```

**Benefícios**:
- Testabilidade (mock de dependências)
- Flexibilidade (trocar implementações)
- Clareza (dependências explícitas)

### 2. Adapter Pattern

Adapters encapsulam integrações com sistemas externos:

```python
class OpenAIAdapter:
    """Adapter para OpenAI API"""
    
class ChromaDBAdapter:
    """Adapter para ChromaDB"""
```

**Benefícios**:
- Isola lógica de integração
- Facilita testes (mock adapters)
- Permite trocar implementações

### 3. Repository Pattern

ChromaDBAdapter atua como repository:

```python
class ChromaDBAdapter:
    def search(self, query: str) -> List[Document]
    def add_documents(self, docs: List[Document])
    def delete_collection(self)
```

**Benefícios**:
- Abstrai acesso a dados
- Centraliza operações de persistência
- Facilita troca de banco de dados

### 4. Strategy Pattern

Diferentes estratégias de chunking:

```python
class ChunkingStrategy(Enum):
    RECURSIVE = "recursive"
    CHARACTER = "character"
    SEMANTIC = "semantic"
```

**Benefícios**:
- Fácil adicionar novas estratégias
- Configurável via enum
- Encapsula algoritmos

### 5. Template Method (ReAct)

Agente segue template do ReAct:

```python
def react_loop():
    while not done:
        thought = llm.think()
        action = llm.choose_action()
        observation = execute_tool(action)
        if has_enough_info(observation):
            return llm.final_answer()
```

---

## Princípios SOLID

### Single Responsibility Principle (SRP)
Cada classe tem uma responsabilidade:
- `Config`: Apenas configuração
- `DocumentLoader`: Apenas carregamento
- `AuditorAgent`: Apenas lógica do agente

### Open/Closed Principle (OCP)
Aberto para extensão, fechado para modificação:
- Adicionar nova tool sem modificar agent
- Adicionar novo adapter sem modificar core

### Liskov Substitution Principle (LSP)
Subclasses podem substituir classes base:
- Todas as exceções herdam de `AuditorError`
- Adapters seguem interfaces consistentes

### Interface Segregation Principle (ISP)
Interfaces específicas e focadas:
- `ChunkingProtocol` define apenas `split()`
- Tools definem apenas `name`, `func`, `description`

### Dependency Inversion Principle (DIP)
Dependa de abstrações, não de implementações:
- Agent depende de adapters (abstrações)
- Main depende de interfaces, não de classes concretas

---

## Benefícios da Arquitetura

### 1. Testabilidade
- Componentes isolados
- Fácil mock de dependências
- Testes unitários independentes

### 2. Manutenibilidade
- Responsabilidades claras
- Código organizado
- Fácil localizar bugs

### 3. Escalabilidade
- Fácil adicionar features
- Componentes reutilizáveis
- Paralelização possível

### 4. Flexibilidade
- Trocar LLM provider
- Trocar vector database
- Adicionar novos adapters

---

## Extensões Futuras

### Adicionar Nova Tool

```python
# domain/tools.py
def calculate_risk_score(contract_data: str) -> str:
    # Implementação
    return risk_score

tools.append(Tool(
    name="calculate_risk",
    func=calculate_risk_score,
    description="Calculate risk score"
))
```

### Adicionar Novo Adapter

```python
# adapters/pinecone_adapter.py
class PineconeAdapter:
    def __init__(self, config):
        # Implementação
        
    def search(self, query: str) -> List[Document]:
        # Busca no Pinecone
```

### Adicionar Memory

```python
# core/memory.py
class ConversationMemory:
    def add_message(self, message: str)
    def get_context(self) -> str
    def clear(self)
```

---

**Bootcamp Itaú FIAP 2026** | Documentação da Arquitetura
