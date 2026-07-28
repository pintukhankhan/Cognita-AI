# Cognita
> *Knowledge, reasoned.* — a production‑grade, knowledge‑grounded conversational AI agent.

Cognita combines hybrid retrieval (vector + graph), LLM‑as‑judge reranking,
intent‑aware routing, guardrails, conversation memory, and streaming (SSE + WebSocket)
behind a single stateless FastAPI service.

## Quickstart
```bash
make install          # venv + deps + docker + migrate
echo "hello world" > data/corpus/intro.txt
make seed             # ingest corpus into the vector store
make run              # uvicorn with reload
make test             # unit + integration + e2e
