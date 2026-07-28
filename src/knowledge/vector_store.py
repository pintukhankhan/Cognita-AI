from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Optional
import structlog
from pinecone import Pinecone
from src.config.settings import settings
from src.services.embedding_service import EmbeddingService

logger = structlog.get_logger(__name__)


class VectorStoreService:
    def __init__(self, embedding_service: EmbeddingService):
        self.embed = embedding_service
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        names = [n.name if hasattr(n, "name") else n for n in self.pc.list_indexes()]
        if settings.PINECONE_INDEX_NAME not in names:
            self.pc.create_index(name=settings.PINECONE_INDEX_NAME,
                                 dimension=settings.EMBEDDING_DIM, metric="cosine")
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
        logger.info("cognita.vector_store.ready", index=settings.PINECONE_INDEX_NAME)

    async def add_documents(self, documents: List[Dict[str, Any]], namespace: Optional[str] = None) -> List[str]:
        ns = namespace or "default"
        texts = [d["text"] for d in documents]
        vecs = [d["embedding"] for d in documents if "embedding" in d]
        if len(vecs) != len(texts):
            vecs = await self.embed.embed(texts)
        payload = [{"id": d["id"], "values": vecs[i],
                    "metadata": {**d.get("metadata", {}), "text": texts[i][:1000]}}
                   for i, d in enumerate(documents)]
        await asyncio.to_thread(self.index.upsert, vectors=payload, namespace=ns)
        return [d["id"] for d in documents]

    async def similarity_search(self, query: str, k: int = 5, filter: Optional[Dict] = None,
                                namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        ns = namespace or "default"
        qv = await self.embed.embed_query(query)
        res = await asyncio.to_thread(self.index.query, vector=qv, top_k=k,
                                      include_metadata=True, namespace=ns, filter=filter)
        return [{"id": m.id, "text": m.metadata.get("text", ""),
                 "metadata": {k_: v for k_, v in m.metadata.items() if k_ != "text"},
                 "score": m.score} for m in res.matches]

    async def delete_documents(self, ids: List[str], namespace: Optional[str] = None) -> bool:
        await asyncio.to_thread(self.index.delete, ids=ids, namespace=namespace or "default")
        return True

    async def delete_all(self, namespace: Optional[str] = None) -> bool:
        await asyncio.to_thread(self.index.delete, delete_all=True, namespace=namespace or "default")
        return True
