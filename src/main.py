from __future__ import annotations
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from src.config.settings import settings
from src.config.logging_config import setup_logging
from src.config.redis import create_redis

from src.services.llm_service import LLMService
from src.services.embedding_service import EmbeddingService
from src.services.cache_manager import ResponseCache
from src.services.cost_tracker import CostTracker
from src.services.guardrails import Guardrails
from src.services.document_processor import DocumentProcessor, DocumentIngestionPipeline
from src.utils.metrics import MetricsCollector
from src.api.middleware.rate_limit import RateLimiter, rate_limit_middleware

from src.knowledge.vector_store import VectorStoreService
from src.knowledge.graph_store import GraphStoreService
from src.knowledge.retriever import HybridRetriever
from src.knowledge.reranker import LLMReranker

from src.agents.memory_manager import MemoryManager
from src.agents.reasoning_engine import ReasoningEngine
from src.agents.intent_router import IntentRouter
from src.agents.summarizer import ConversationSummarizer
from src.agents.orchestrator import AgentOrchestrator
from src.agents.tools.tool_registry import default_registry

from src.api.routes import chat, health, admin, documents, ws_chat

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.DEBUG)
    logger.info("cognita.boot.start", version=settings.APP_VERSION)
    s: dict = {}

    redis = create_redis()
    s["llm"] = LLMService()
    s["embeddings"] = EmbeddingService(redis)
    s["memory_manager"] = MemoryManager(redis)
    s["vector_store"] = VectorStoreService(s["embeddings"])
    s["graph_store"] = GraphStoreService()
    s["response_cache"] = ResponseCache(redis)
    s["cost_tracker"] = CostTracker()
    s["guardrails"] = Guardrails()
    s["metrics_collector"] = MetricsCollector()
    s["rate_limiter"] = RateLimiter(redis)
    s["document_processor"] = DocumentProcessor()
    s["ingestion_pipeline"] = DocumentIngestionPipeline(s["vector_store"], s["document_processor"])

    s["retriever"] = HybridRetriever(s["vector_store"], s["graph_store"])
    s["reranker"] = LLMReranker(s["llm"])
    s["intent_router"] = IntentRouter(s["llm"], default_registry.names())
    s["summarizer"] = ConversationSummarizer(s["llm"])
    s["reasoning_engine"] = ReasoningEngine(s["llm"])
    s["orchestrator"] = AgentOrchestrator(
        memory_manager=s["memory_manager"], reasoning_engine=s["reasoning_engine"],
        retriever=s["retriever"], llm=s["llm"], intent_router=s["intent_router"],
        reranker=s["reranker"], guardrails=s["guardrails"], summarizer=s["summarizer"],
        cost_tracker=s["cost_tracker"], metrics=s["metrics_collector"])

    app.state.services = s
    logger.info("cognita.boot.ready", components=sorted(s.keys()))
    yield
    await s["graph_store"].close()
    await s["memory_manager"].close()
    logger.info("cognita.boot.shutdown")


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION,
              description="Cognita — knowledge, reasoned.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.middleware("http")(rate_limit_middleware)


@app.middleware("http")
async def instrument(request: Request, call_next):
    t0 = time.perf_counter()
    try:
        resp = await call_next(request)
    except Exception as e:
        logger.error("cognita.http.unhandled", error=str(e), path=request.url.path)
        return JSONResponse(status_code=500, content={"detail": "internal_error"})
    svc = getattr(app.state, "services", None)
    if svc:
        svc["metrics_collector"].record_request(request.method, request.url.path,
                                                resp.status_code, (time.perf_counter() - t0) * 1000)
    return resp


app.include_router(health.router,    prefix=f"{settings.API_V1_PREFIX}/health", tags=["Health"])
app.include_router(chat.router,      prefix=f"{settings.API_V1_PREFIX}/chat",   tags=["Chat"])
app.include_router(ws_chat.router,   prefix=f"{settings.API_V1_PREFIX}",        tags=["WS"])
app.include_router(documents.router, prefix=f"{settings.API_V1_PREFIX}/docs",   tags=["Docs"])
app.include_router(admin.router,     prefix=f"{settings.API_V1_PREFIX}/admin",  tags=["Admin"])


@app.get("/")
async def root():
    return {"app": settings.APP_NAME, "tagline": "Knowledge, reasoned.",
            "version": settings.APP_VERSION, "docs": "/docs"}
