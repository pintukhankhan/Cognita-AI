from __future__ import annotations
import asyncio, time
from typing import Dict
from fastapi import APIRouter, Request
from pydantic import BaseModel
from src.config.settings import settings

router = APIRouter()
_START = time.time()


class Comp(BaseModel):
    status: str; latency_ms: float; detail: str = ""


class Health(BaseModel):
    status: str; version: str; uptime_seconds: float; components: Dict[str, Comp] = {}


async def _redis(r):
    t = time.perf_counter()
    try:
        await r.ping(); return Comp(status="up", latency_ms=(time.perf_counter() - t) * 1000)
    except Exception as e:
        return Comp(status="down", latency_ms=(time.perf_counter() - t) * 1000, detail=str(e))


async def _neo4j(d):
    t = time.perf_counter()
    try:
        async with d.session() as s:
            await s.run("RETURN 1")
        return Comp(status="up", latency_ms=(time.perf_counter() - t) * 1000)
    except Exception as e:
        return Comp(status="down", latency_ms=(time.perf_counter() - t) * 1000, detail=str(e))


async def _pine(idx):
    t = time.perf_counter()
    try:
        st = await asyncio.to_thread(idx.describe_index_stats)
        n = getattr(st, "total_vector_count", 0)
        return Comp(status="up", latency_ms=(time.perf_counter() - t) * 1000, detail=f"vectors={n}")
    except Exception as e:
        return Comp(status="down", latency_ms=(time.perf_counter() - t) * 1000, detail=str(e))


@router.get("/", response_model=Health)
@router.get("/live", response_model=Health)
async def live(req: Request):
    return Health(status="ok", version=settings.APP_VERSION, uptime_seconds=time.time() - _START)


@router.get("/ready", response_model=Health)
async def ready(req: Request):
    s = req.app.state.services
    c = await asyncio.gather(_redis(s["memory_manager"].redis), _neo4j(s["graph_store"].driver),
                             _pine(s["vector_store"].index))
    comps = {"redis": c[0], "neo4j": c[1], "pinecone": c[2]}
    return Health(status="ok" if all(x.status == "up" for x in comps.values()) else "degraded",
                  version=settings.APP_VERSION, uptime_seconds=time.time() - _START, components=comps)
