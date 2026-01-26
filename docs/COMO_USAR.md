# 🚀 Como Usar o Auditor de Contratos

Guia rápido de uso para as duas versões disponíveis.

---

## 📁 Estrutura do Projeto

```
auditor-contratos/
├── v1/                    # ← Versão DIDÁTICA (simples)
│   └── auditor_contratos.py
│
├── adapters/              # ← Versão PROFISSIONAL (refatorada)
├── core/
├── domain/
└── main.py
```

---

## 🎓 Versão 1 - Didática (Recomendada para Iniciantes)

### Para que serve?
- Aprender conceitos de RAG e agentes
- Entender o fluxo completo em um arquivo
- Fazer testes rápidos

### Como usar?

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Executar
python v1/auditor_contratos.py
```

### Arquivos úteis em v1/
- `auditor_contratos.py` - Código principal
- `test_setup.py` - Testar instalação
- `exemplo_uso_avancado.py` - 6 exemplos práticos
- `utils.py` - Utilitários (limpar ChromaDB, etc)

---

## 🏭 Versão Profissional (Recomendada para Produção)

### Para que serve?
- Projetos reais e produção
- Trabalho em equipe
- Código escalável e testável

### Como usar?

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Executar
python main.py
```

### Estrutura modular
- `adapters/` - Integrações (OpenAI, ChromaDB)
- `core/` - Lógica principal (Agent, Config)
- `domain/` - Modelos de negócio (Schema, Tools)
- `tests/` - Testes unitários

---

## ⚙️ Configuração Inicial

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar API Key

Crie arquivo `.env` na **raiz** do projeto:

```bash
OPENAI_API_KEY=sk-sua-chave-aqui
```

### 3. Testar Instalação

```bash
python v1/test_setup.py
```

---

## 🎯 Casos de Uso

### Analisar um Contrato

**v1 (Simples):**
```bash
# Usa contrato de exemplo
python v1/auditor_contratos.py
```

**Versão Profissional:**
```bash
# Usa contrato de exemplo
python main.py
```

### Usar Seu Próprio Contrato

1. Coloque seu PDF/TXT na pasta `v1/`
2. Edite o path no código:

**v1:**
```python
# Em v1/auditor_contratos.py, linha ~300
contract_path = "meu_contrato.pdf"
```

**Versão Profissional:**
```python
# Em main.py, linha ~50
contract_path = "v1/meu_contrato.pdf"
```

### Limpar ChromaDB

```bash
python v1/utils.py
# Escolha opção 1: Limpar ChromaDB
```

Ou manualmente:
```bash
rm -rf chroma_db  # Linux/Mac
rmdir /s chroma_db  # Windows
```

---

## 🧪 Executar Testes

### Versão Profissional

```bash
# Todos os testes
pytest tests/

# Teste específico
pytest tests/test_config.py

# Com cobertura
pytest tests/ --cov=.

# Verbose
pytest tests/ -v
```

---

## 📊 Ver Estatísticas

```bash
python v1/utils.py
# Escolha opção 3: Estatísticas do Projeto
```

---

## 🔧 Customizações

### Alterar Tamanho dos Chunks

**v1:**
```python
# Em v1/auditor_contratos.py
vectorstore = ingest_contract(
    "contrato.pdf",
    chunk_size=1000,  # ← Alterar aqui
    chunk_overlap=100
)
```

**Versão Profissional:**
```bash
# No arquivo .env
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
```

### Usar Modelo Diferente

**No arquivo .env:**
```bash
OPENAI_MODEL=gpt-3.5-turbo  # Mais barato
# ou
OPENAI_MODEL=gpt-4-turbo-preview  # Melhor qualidade
```

### Aumentar Iterações do Agente

**No arquivo .env:**
```bash
MAX_ITERATIONS=15  # Padrão: 10
```

---

## 🐛 Troubleshooting Rápido

### "OPENAI_API_KEY não encontrada"
→ Crie arquivo `.env` na raiz com a chave

### "ChromaDB locked"
→ Execute: `rm -rf chroma_db`

### "ModuleNotFoundError"
→ Ative venv e instale: `pip install -r requirements.txt`

### Agente em loop infinito
→ Reduza MAX_ITERATIONS no .env

---

## 📚 Mais Informações

- **Conceitos**: Abra `index.html` no navegador
- **Documentação v1**: `v1/README.md`
- **Arquitetura**: `docs/ARQUITETURA.md`
- **Quickstart**: `docs/QUICKSTART.md`
- **Instalação**: `docs/INSTALACAO.md`

---

## 🎓 Fluxo de Aprendizado Recomendado

```
1. Execute v1/test_setup.py
   └─► Garante que tudo está configurado

2. Execute python v1/auditor_contratos.py
   └─► Entenda o fluxo básico

3. Leia v1/auditor_contratos.py
   └─► Veja o código (~350 linhas)

4. Execute python v1/exemplo_uso_avancado.py
   └─► Explore casos de uso

5. Execute python main.py
   └─► Veja versão profissional

6. Compare v1/ com raiz/
   └─► Entenda a refatoração

7. Abra index.html
   └─► Estude teoria completa
```

---

**💡 Dica Final**: Comece simples (v1), depois evolua para profissional!

**Bootcamp Itaú FIAP 2026**
