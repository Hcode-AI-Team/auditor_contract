# 🚀 Quickstart - Auditor de Contratos

Guia rápido para começar em 5 minutos!

## ⚡ Setup Rápido

```bash
# 1. Criar ambiente virtual
python -m venv venv

# 2. Ativar (Windows)
venv\Scripts\activate

# 2. Ativar (Linux/Mac)
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Criar arquivo .env
echo "OPENAI_API_KEY=sk-sua-chave-aqui" > .env

# 5. Executar
python auditor_contratos.py
```

## 📊 O que acontece ao executar?

### Passo 1: Ingestão
```
📄 Carregando documento: contrato_mutuo_exemplo.txt
   ✓ 1 página(s) carregada(s)
   ✓ 12 chunks criados
🔄 Gerando embeddings e indexando no ChromaDB...
✅ Indexados 12 chunks no ChromaDB
```

### Passo 2: Criação do Agente
```
🤖 ETAPA 2: Criação do Agente ReAct
✅ Agente auditor criado e pronto!
```

### Passo 3: Análise (ReAct Loop)
```
🔍 ETAPA 3: Análise do Contrato

> Entering new AgentExecutor chain...

Thought: Preciso buscar informações sobre garantias
Action: search_contract
Action Input: "garantias tipo objeto"
Observation: Chunks encontrados:
Chunk 1:
CLÁUSULA QUARTA - DAS GARANTIAS
4.1. Como garantia fiel do cumprimento das obrigações...

Thought: Preciso buscar valores e prazos
Action: search_contract
Action Input: "valor principal prazo meses"
Observation: Chunks encontrados:
...

Thought: Agora tenho informação suficiente
Final Answer: {
  "garantia_tipo": "Alienação Fiduciária",
  "garantia_objeto": "Imóvel Matrícula 12345 do 2º CRI São Paulo",
  ...
}
```

### Resultado Final
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

## 🎮 Testando com seu próprio PDF

Substitua `contrato_mutuo_exemplo.txt` por seu PDF:

```python
# No código auditor_contratos.py, linha 300:
contract_path = "seu_contrato.pdf"
```

Ou simplesmente renomeie seu PDF para `contrato_mutuo.pdf` na raiz do projeto.

## 🔧 Customizações Rápidas

### Ajustar tamanho dos chunks
```python
# linha 289 em auditor_contratos.py
vectorstore = ingest_contract(
    contract_path,
    chunk_size=1000,  # ← aumentar para chunks maiores
    chunk_overlap=100
)
```

### Usar modelo mais barato
```python
# linha 210 em auditor_contratos.py
llm = ChatOpenAI(
    model="gpt-3.5-turbo",  # ← mais barato que gpt-4
    temperature=0
)
```

### Buscar mais chunks por query
```python
# linha 147 em auditor_contratos.py
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 5}  # ← aumentar de 3 para 5
)
```

## 💰 Custos Estimados (OpenAI)

Para 1 contrato de ~2 páginas:

| Componente | Tokens | Custo (USD) |
|------------|--------|-------------|
| Embeddings (text-embedding-3-small) | ~1,500 | $0.0002 |
| Análise GPT-4 (5 iterações) | ~3,000 | $0.09 |
| **TOTAL** | | **~$0.10** |

💡 Use GPT-3.5-turbo para reduzir custo para ~$0.01 por análise.

## ❓ Perguntas Customizadas

Altere a query no `main()`:

```python
# Exemplo: Análise de compliance específica
query = """
Verifique se este contrato está em compliance com:
1. Taxa de juros máxima de 2% ao mês
2. Prazo mínimo de 12 meses
3. Garantia real obrigatória para valores > R$ 500k

Retorne JSON com os campos padrão do ContractMetadata.
"""

result = agent.invoke({"input": query})
```

## 🐛 Erros Comuns

### `ModuleNotFoundError: No module named 'langchain'`
→ Você esqueceu de ativar o venv: `venv\Scripts\activate`

### `ValueError: OPENAI_API_KEY não encontrada`
→ Crie o arquivo `.env` com a chave válida

### `sqlite3.OperationalError: database is locked`
→ Feche outras instâncias do script e delete `chroma_db/`

### Agente retorna "Final Answer" incompleta
→ Aumente `max_iterations` no AgentExecutor (linha 263)

## 📈 Próximos Passos

1. ✅ Rode o exemplo básico
2. 📝 Teste com seu próprio contrato PDF
3. 🔧 Ajuste chunk_size e compare resultados
4. 🚀 Implemente os exercícios avançados do `index.html`

---

**Dúvidas?** Abra o `index.html` no navegador para ver todo o material teórico!
