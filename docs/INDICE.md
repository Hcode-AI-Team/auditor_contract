# 📑 Índice do Projeto - Auditor de Contratos

Guia de navegação rápida para todos os arquivos do projeto.

---

## 🚀 Por Onde Começar?

### 1️⃣ Primeira Vez Aqui?
👉 Leia: **[README.md](README.md)** - Visão geral completa do projeto

### 2️⃣ Quer Começar Rápido?
👉 Siga: **[QUICKSTART.md](QUICKSTART.md)** - Setup em 5 minutos

### 3️⃣ Problemas na Instalação?
👉 Consulte: **[INSTALACAO.md](INSTALACAO.md)** - Guia detalhado + troubleshooting

### 4️⃣ Precisa de Referência?
👉 Use: **[REFERENCIA_RAPIDA.md](REFERENCIA_RAPIDA.md)** - Comandos e conceitos

### 5️⃣ Quer Ver o Resumo?
👉 Veja: **[PROJETO_COMPLETO.md](PROJETO_COMPLETO.md)** - Status e arquitetura

---

## 📚 Documentação

| Arquivo | Quando Usar | Tempo de Leitura |
|---------|-------------|------------------|
| [README.md](README.md) | Visão geral e documentação completa | 10 min |
| [QUICKSTART.md](QUICKSTART.md) | Começar rapidamente | 5 min |
| [INSTALACAO.md](INSTALACAO.md) | Instalar e configurar | 15 min |
| [REFERENCIA_RAPIDA.md](REFERENCIA_RAPIDA.md) | Consultar comandos | 5 min |
| [PROJETO_COMPLETO.md](PROJETO_COMPLETO.md) | Ver status e arquitetura | 8 min |
| [INDICE.md](INDICE.md) | Navegar pelos arquivos | 2 min |

---

## 🐍 Código Python

### Arquivo Principal
- **[auditor_contratos.py](auditor_contratos.py)** - Sistema completo de auditoria
  - `ingest_contract()` - Ingestão de documentos
  - `create_tools()` - Definição de tools
  - `create_auditor_agent()` - Criação do agente ReAct
  - `ContractMetadata` - Schema Pydantic
  - `main()` - Execução principal

### Scripts Auxiliares
- **[test_setup.py](test_setup.py)** - Validação de instalação
  - Testa Python, dependências, API Key, conexão
  
- **[exemplo_uso_avancado.py](exemplo_uso_avancado.py)** - 6 exemplos práticos
  - Análise básica
  - Query customizada
  - Múltiplos contratos
  - Validação Pydantic
  - Busca direta
  - Configurações customizadas

- **[utils.py](utils.py)** - Utilitários
  - `limpar_chromadb()` - Limpar banco vetorial
  - `listar_collections()` - Ver collections
  - `estatisticas_projeto()` - Estatísticas
  - `criar_contrato_teste()` - Gerar contrato de teste

---

## ⚙️ Configuração

| Arquivo | Descrição |
|---------|-----------|
| [requirements.txt](requirements.txt) | Dependências do projeto |
| `.env` | Variáveis de ambiente (criar manualmente) |
| `.gitignore` | Arquivos ignorados pelo Git |

---

## 📄 Dados

| Arquivo | Descrição |
|---------|-----------|
| [contrato_mutuo_exemplo.txt](contrato_mutuo_exemplo.txt) | Contrato de exemplo para testes |
| `chroma_db/` | Banco vetorial (gerado automaticamente) |

---

## 📖 Material Didático

| Arquivo | Descrição |
|---------|-----------|
| [index.html](index.html) | Material teórico completo sobre RAG e Agentes |

💡 **Dica**: Abra o `index.html` no navegador para ver todo o conteúdo teórico interativo!

---

## 🎯 Fluxo de Uso Recomendado

### Para Iniciantes

```
1. Leia README.md (visão geral)
   ↓
2. Siga INSTALACAO.md (setup completo)
   ↓
3. Execute: python test_setup.py
   ↓
4. Execute: python auditor_contratos.py
   ↓
5. Explore: python exemplo_uso_avancado.py
   ↓
6. Estude: index.html (teoria)
```

### Para Desenvolvedores

```
1. Leia QUICKSTART.md (setup rápido)
   ↓
2. Execute: python auditor_contratos.py
   ↓
3. Leia código: auditor_contratos.py
   ↓
4. Customize: Adicione tools, modifique schema
   ↓
5. Consulte: REFERENCIA_RAPIDA.md
```

### Para Troubleshooting

```
1. Execute: python test_setup.py
   ↓
2. Consulte: INSTALACAO.md (seção Problemas Comuns)
   ↓
3. Use: python utils.py (limpar ChromaDB)
   ↓
4. Veja: REFERENCIA_RAPIDA.md (seção Troubleshooting)
```

---

## 🔍 Busca Rápida

### Quero saber sobre...

**Instalação**
- Passo a passo: [INSTALACAO.md](INSTALACAO.md)
- Rápido: [QUICKSTART.md](QUICKSTART.md)

**Conceitos**
- RAG: [README.md](README.md#arquitetura-do-sistema)
- ReAct: [REFERENCIA_RAPIDA.md](REFERENCIA_RAPIDA.md#conceitos-chave)
- Chunking: [README.md](README.md#componentes-principais)

**Código**
- Ingestão: [auditor_contratos.py](auditor_contratos.py) linha 80
- Agente: [auditor_contratos.py](auditor_contratos.py) linha 200
- Tools: [auditor_contratos.py](auditor_contratos.py) linha 140
- Schema: [auditor_contratos.py](auditor_contratos.py) linha 40

**Exemplos**
- Uso básico: [exemplo_uso_avancado.py](exemplo_uso_avancado.py) linha 15
- Query custom: [exemplo_uso_avancado.py](exemplo_uso_avancado.py) linha 40
- Validação: [exemplo_uso_avancado.py](exemplo_uso_avancado.py) linha 120

**Problemas**
- Erros comuns: [INSTALACAO.md](INSTALACAO.md#problemas-comuns)
- Troubleshooting: [REFERENCIA_RAPIDA.md](REFERENCIA_RAPIDA.md#troubleshooting-rápido)

**Configuração**
- Dependências: [requirements.txt](requirements.txt)
- API Key: [INSTALACAO.md](INSTALACAO.md#passo-5-configurar-variáveis-de-ambiente)
- Parâmetros: [REFERENCIA_RAPIDA.md](REFERENCIA_RAPIDA.md#parâmetros-configuráveis)

---

## 📊 Estatísticas do Projeto

### Código
- **5 arquivos Python** (~1.050 linhas)
- **0 erros de linting**
- **100% documentado**

### Documentação
- **6 arquivos Markdown**
- **~3.000 linhas de documentação**
- **Cobertura completa**

### Funcionalidades
- **2 tools implementadas**
- **7 campos de metadados**
- **6 exemplos práticos**
- **4 utilitários**

---

## 🎓 Recursos de Aprendizado

### Teoria
1. **[index.html](index.html)** - Material didático completo
   - Fundamentos de RAG
   - Estratégias de chunking
   - Embedding models
   - Vector databases
   - Agentes ReAct
   - Exercícios práticos

### Prática
1. **[auditor_contratos.py](auditor_contratos.py)** - Código comentado
2. **[exemplo_uso_avancado.py](exemplo_uso_avancado.py)** - 6 exemplos
3. **[test_setup.py](test_setup.py)** - Validação

### Referência
1. **[REFERENCIA_RAPIDA.md](REFERENCIA_RAPIDA.md)** - Comandos e conceitos
2. **[README.md](README.md)** - Documentação completa

---

## 🚀 Próximos Passos

Após explorar o projeto:

1. ✅ **Teste com seus contratos**
   - Substitua o PDF de exemplo
   - Ajuste chunk_size conforme necessário

2. ✅ **Implemente exercícios avançados**
   - Hybrid Search (BM25 + embeddings)
   - Memory conversacional
   - Multi-Document RAG

3. ✅ **Customize para seu caso de uso**
   - Adicione novas tools
   - Modifique o schema
   - Ajuste o prompt do agente

4. ✅ **Estude o material teórico**
   - Abra `index.html` no navegador
   - Complete os exercícios propostos

---

## 📞 Ajuda e Suporte

### Dúvidas Técnicas
- Consulte: [REFERENCIA_RAPIDA.md](REFERENCIA_RAPIDA.md)
- Veja: [INSTALACAO.md](INSTALACAO.md) (Problemas Comuns)

### Dúvidas Conceituais
- Leia: [README.md](README.md)
- Estude: [index.html](index.html)

### Problemas de Código
- Execute: `python test_setup.py`
- Use: `python utils.py` (opção 3 - Estatísticas)

---

## ✅ Checklist de Uso

### Primeira Execução
- [ ] Ler README.md
- [ ] Seguir INSTALACAO.md
- [ ] Executar test_setup.py
- [ ] Executar auditor_contratos.py
- [ ] Verificar output JSON

### Desenvolvimento
- [ ] Estudar auditor_contratos.py
- [ ] Testar exemplo_uso_avancado.py
- [ ] Customizar para seu caso
- [ ] Implementar exercícios avançados

### Produção
- [ ] Configurar .env seguro
- [ ] Ajustar parâmetros (chunk_size, k, etc)
- [ ] Testar com contratos reais
- [ ] Validar outputs
- [ ] Monitorar custos OpenAI

---

**🎉 Projeto completo e pronto para uso!**

Escolha seu ponto de partida acima e comece a explorar! 🚀

---

**Bootcamp Itaú FIAP 2026** | Última atualização: Janeiro 2026
