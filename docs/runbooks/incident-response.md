# Cognita — Incident Response
- P0 <5m: service down / data loss / breach
- P1 <15m: error rate >10% / major feature broken
Steps: detect → communicate → investigate → mitigate (rollback/scale) → resolve → post-mortem (48h).
High latency: check cache hit rate, DB pool, external APIs, then scale HPA.
