# Cognita — Architecture
Layered: API → Security → Orchestration → Intelligence → Knowledge → Services → Infra.
Request flow: auth → rate-limit → orchestrator(intent → retrieve → rerank → reason → guard → memory).
State is externalized (Redis, Pinecone, Neo4j) so the API tier is stateless & horizontally scalable.
