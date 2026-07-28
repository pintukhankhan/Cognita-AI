from __future__ import annotations
from typing import Any, Dict, List, Optional
import structlog
from neo4j import AsyncGraphDatabase
from src.config.settings import settings

logger = structlog.get_logger(__name__)


class GraphStoreService:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(settings.NEO4J_URI,
                                                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))

    async def close(self) -> None:
        await self.driver.close()

    async def add_triplet(self, subject: str, relation: str, obj: str,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        q = """MERGE (s:Entity {name:$s}) MERGE (o:Entity {name:$o})
               MERGE (s)-[r:REL {type:$rel}]->(o) SET r+=$meta RETURN s"""
        async with self.driver.session() as sess:
            await sess.run(q, s=subject, o=obj, rel=relation, meta=metadata or {})
        return True

    async def query(self, text: str, limit: int = 10) -> List[Dict[str, Any]]:
        q = """CALL db.index.fulltext.queryNodes('entityIndex',$t) YIELD node,score
               MATCH (node)-[r]->(x)
               RETURN node.name AS subject, type(r) AS relation, x.name AS object, score
               LIMIT $lim"""
        try:
            async with self.driver.session() as sess:
                res = await sess.run(q, t=text, lim=limit)
                return [{"subject": r["subject"], "relation": r["relation"],
                         "object": r["object"], "score": r["score"]} async for r in res]
        except Exception as e:
            logger.warning("cognita.graph.query_failed", error=str(e))
            return []
