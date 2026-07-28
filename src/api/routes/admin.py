from __future__ import annotations
import asyncio
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from src.api.middleware.auth import require_role

router = APIRouter()


class IngestReq(BaseModel):
    source: str
    namespace: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Stats(BaseModel):
    active_sessions: int; total_vectors: int; cache_hit_rate: float
    avg_latency_ms: float; error_rate: float; window_minutes: int


@router.get("/stats", response_model=Stats, dependencies=[Depends(require_role("admin"))])
async def stats(req: Request, window: int = Query(60, ge=1, le=1440)):
    s = req.app.state.services
    cache = await s["response_cache"].get_stats()
    snap = s["metrics_collector"].snapshot(window)
    st = await asyncio.to_thread(s["vector_store"].index.describe_index_stats)
    return Stats(active_sessions=snap["active_sessions"],
                 total_vectors=getattr(st, "total_vector_count", 0),
                 cache_hit_rate=cache["hit_rate"], avg_latency_ms=snap["avg_latency_ms"],
                 error_rate=snap["error_rate"], window_minutes=window)


@router.post("/ingest", dependencies=[Depends(require_role("admin"))])
async def ingest(req: Request, body: IngestReq):
    pipe = req.app.state.services["ingestion_pipeline"]
    return await pipe.ingest_source(body.source, body.namespace, body.metadata)


@router.delete("/namespace/{namespace}", dependencies=[Depends(require_role("admin"))])
async def del_ns(req: Request, namespace: str):
    await req.app.state.services["vector_store"].delete_all(namespace=namespace)
    return {"status": "deleted", "namespace": namespace}


@router.post("/reindex", dependencies=[Depends(require_role("admin"))])
async def reindex(req: Request, namespace: Optional[str] = None):
    tid = await req.app.state.services["ingestion_pipeline"].schedule_reindex(namespace=namespace)
    return {"status": "scheduled", "task_id": tid}
