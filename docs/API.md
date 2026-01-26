# API REST - Auditor de Contratos

Documentação da API REST para auditoria de contratos bancários.

## Início Rápido

### Executar Localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar API
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Acessar documentação
# http://localhost:8000/docs
```

### Executar com Docker

```bash
# Build
docker build -t auditor-contratos .

# Run
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... auditor-contratos
```

### Stack Completa (API + Prometheus + Grafana)

```bash
# Iniciar stack
docker-compose up -d

# Acessar:
# - API: http://localhost:8000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

## Endpoints

### Health Check

```http
GET /health
```

Verifica status da aplicação e componentes.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "components": {
    "api": true,
    "openai": true,
    "chromadb": true
  },
  "timestamp": "2026-01-25T10:30:00Z"
}
```

### Métricas Prometheus

```http
GET /metrics
```

Retorna métricas no formato Prometheus para scraping.

**Response (text/plain):**
```
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/health"} 42
# TYPE cache_hits counter
cache_hits 150
# TYPE auditor_analysis_duration_seconds summary
auditor_analysis_duration_seconds_count 10
auditor_analysis_duration_seconds_avg 2.5
```

### Métricas JSON

```http
GET /metrics/json
```

Retorna métricas em formato JSON para debugging.

### Análise de Contrato

```http
POST /api/v1/analyze
```

Inicia análise de um contrato. Retorna imediatamente com ID para consulta posterior.

**Request:**
```json
{
  "contract_path": "v1/contrato_mutuo_exemplo.txt",
  "use_hybrid_search": true,
  "custom_query": null
}
```

Ou com texto direto:

```json
{
  "contract_text": "CONTRATO DE MÚTUO...",
  "use_hybrid_search": true
}
```

**Response:**
```json
{
  "id": "abc-123",
  "status": "pending",
  "created_at": "2026-01-25T10:30:00Z"
}
```

### Consultar Análise

```http
GET /api/v1/analyze/{analysis_id}
```

Consulta resultado de uma análise.

**Response (completa):**
```json
{
  "id": "abc-123",
  "status": "completed",
  "metadata": {
    "garantia_tipo": "Hipoteca",
    "garantia_objeto": "Imóvel residencial",
    "taxa_juros": 5.5,
    "prazo_meses": 36,
    "valor_principal": 100000.0,
    "risco_legal": "Baixo",
    "compliance_check": true,
    "observacoes": "Contrato em conformidade"
  },
  "statistics": {
    "total_steps": 5,
    "tools_used": ["search_contract", "extract_clause"]
  },
  "created_at": "2026-01-25T10:30:00Z",
  "completed_at": "2026-01-25T10:30:15Z",
  "duration_seconds": 15.2
}
```

### Busca no Contrato

```http
POST /api/v1/search
```

Busca informações no contrato indexado.

**Request:**
```json
{
  "query": "taxa de juros",
  "k": 5,
  "use_hybrid": true
}
```

**Response:**
```json
{
  "query": "taxa de juros",
  "results": [
    {
      "content": "A taxa de juros acordada é de 5.5% ao ano...",
      "score": 0.92,
      "semantic_score": 0.95,
      "keyword_score": 0.88,
      "rank": 1
    }
  ],
  "total_results": 1,
  "search_type": "hybrid"
}
```

### Ingestão de Documento

```http
POST /api/v1/ingest
```

Ingere novo documento no sistema.

**Request:**
```json
{
  "file_path": "contratos/novo_contrato.txt",
  "chunk_size": 500,
  "chunk_overlap": 50
}
```

**Response:**
```json
{
  "file_path": "contratos/novo_contrato.txt",
  "num_chunks": 15,
  "chunk_size": 500,
  "chunk_overlap": 50,
  "success": true,
  "message": "Documento processado: 15 chunks indexados"
}
```

### Cache de Embeddings

```http
GET /api/v1/cache/stats
```

Estatísticas do cache de embeddings.

**Response:**
```json
{
  "l1_hits": 150,
  "l1_misses": 20,
  "l1_size": 100,
  "l1_hit_rate": 0.88,
  "model": "text-embedding-3-small"
}
```

```http
DELETE /api/v1/cache
```

Limpa o cache de embeddings.

## Busca Híbrida

A API suporta busca híbrida que combina:

1. **Busca Semântica (ChromaDB)**: Encontra documentos semanticamente similares
2. **Busca por Palavras-chave (BM25)**: Encontra documentos com termos correspondentes

Os resultados são combinados usando **Reciprocal Rank Fusion (RRF)**:

```
RRF_score = α × RRF_semantic + (1 - α) × RRF_keyword
```

Onde `α` (alpha) é o peso dado à busca semântica (padrão: 0.5).

## Resiliência

### Retry com Backoff

Todas as chamadas à OpenAI têm retry automático:

- **Max Attempts**: 3
- **Initial Delay**: 1s
- **Max Delay**: 30s
- **Backoff**: Exponencial com jitter

### Circuit Breaker

Protege contra falhas em cascata:

- **Failure Threshold**: 5 falhas para abrir
- **Timeout**: 30s antes de testar novamente
- **Recovery**: 3 sucessos para fechar

## Cache de Embeddings

Sistema de cache em dois níveis:

1. **L1 (Memória)**: Cache rápido em memória (1 hora TTL)
2. **L2 (Disco)**: Cache persistente em disco (7 dias TTL)

Benefícios:
- Reduz custos de API
- Melhora latência em consultas repetidas
- Persiste entre reinícios

## Monitoramento

### Prometheus

Configure o Prometheus para scraping:

```yaml
scrape_configs:
  - job_name: 'auditor-api'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 10s
```

### Grafana

Dashboard pré-configurado inclui:
- Contratos analisados
- Erros de análise
- Cache hit rate
- Tempo de análise
- Requisições HTTP
- Uso de tools

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OPENAI_API_KEY` | API Key da OpenAI | (obrigatório) |
| `LOG_LEVEL` | Nível de log | `INFO` |
| `LOG_FORMAT` | Formato de log (`json`/`pretty`) | `pretty` |
| `LLM_MODEL` | Modelo LLM | `gpt-4o` |
| `EMBEDDING_MODEL` | Modelo de embeddings | `text-embedding-3-small` |
| `CHUNK_SIZE` | Tamanho do chunk | `500` |
| `CHUNK_OVERLAP` | Sobreposição de chunks | `50` |

## Exemplo de Uso com cURL

```bash
# Health check
curl http://localhost:8000/health

# Ingerir documento
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"file_path": "v1/contrato_mutuo_exemplo.txt"}'

# Analisar contrato
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"contract_path": "v1/contrato_mutuo_exemplo.txt"}'

# Consultar análise
curl http://localhost:8000/api/v1/analyze/abc-123

# Buscar no contrato
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "taxa de juros", "k": 3}'

# Métricas
curl http://localhost:8000/metrics
```

## Exemplo com Python

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Ingerir documento
        resp = await client.post("/api/v1/ingest", json={
            "file_path": "v1/contrato_mutuo_exemplo.txt"
        })
        print(f"Ingestão: {resp.json()}")
        
        # Analisar contrato
        resp = await client.post("/api/v1/analyze", json={
            "contract_path": "v1/contrato_mutuo_exemplo.txt",
            "use_hybrid_search": True
        })
        analysis_id = resp.json()["id"]
        print(f"Análise iniciada: {analysis_id}")
        
        # Aguardar conclusão
        while True:
            resp = await client.get(f"/api/v1/analyze/{analysis_id}")
            result = resp.json()
            
            if result["status"] in ["completed", "failed"]:
                break
            
            await asyncio.sleep(1)
        
        print(f"Resultado: {result}")

asyncio.run(main())
```
