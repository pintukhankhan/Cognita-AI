from __future__ import annotations
from typing import Any, Dict, List
import structlog
from src.knowledge.vector_store import VectorStoreService
from src.knowledge.graph_store import GraphStoreService

logger = structlog.get_logger(__name__)


class HybridRetriever:
    def __init__(self, vector_store: VectorStoreService, graph_store: GraphStoreService):
        self.vs, self.gs = vector_store, graph_store

    async def retrieve(self, query: str, top_k: int = 5, use_hybrid: bool = True) -> Dict[str, Any]:
        vr = await self.vs.similarity_search(query, k=top_k)
        gr = await self.gs.query(query, limit=top_k) if use_hybrid else []
        return {"vector_results": vr, "graph_results": gr, "combined_context": self._fmt(vr, gr)}

    def _fmt(self, vr: List[Dict], gr: List[Dict]) -> str:
        parts = []
        if vr:
            parts.append("Relevant Information:\n" + "\n".join(f"[{i + 1}] {d['text']}" for i, d in enumerate(vr)))
        if gr:
            parts.append("Related Knowledge:\n" + "\n".join(f"- {g['subject']} {g['relation']} {g['object']}" for g in gr))
        return "\n\n".join(parts) or "No relevant information found."
