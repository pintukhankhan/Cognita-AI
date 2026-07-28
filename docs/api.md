# Cognita — API Reference
Base: `/api/v1` · Auth header: `X-API-Key`
- `POST /chat/` — sync chat → `{session_id, response, metadata}`
- `POST /chat/stream` — SSE (`event: meta|token|done`)
- `WS /ws?api_key=...` — JSON frames `{type: meta|start|token|end}`
- `GET /health/live`, `GET /health/ready`
- `POST /docs/upload` (multipart `file`), `POST /docs/ingest?source=...`, `DELETE /docs/{id}`
- `GET /admin/stats`, `POST /admin/ingest`, `DELETE /admin/namespace/{ns}`, `POST /admin/reindex` (role: admin)
