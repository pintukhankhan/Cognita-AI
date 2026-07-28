from __future__ import annotations
import shutil, uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from src.api.middleware.auth import verify_api_key

router = APIRouter()
_ALLOWED = {".pdf", ".txt", ".docx", ".doc", ".csv"}


@router.post("/upload", dependencies=[Depends(verify_api_key)])
async def upload(req: Request, file: UploadFile = File(...), namespace: Optional[str] = None):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in _ALLOWED:
        raise HTTPException(400, f"unsupported type {ext}")
    tmp = Path("/tmp") / f"{uuid.uuid4().hex}{ext}"
    try:
        with tmp.open("wb") as b:
            shutil.copyfileobj(file.file, b)
        proc = req.app.state.services["document_processor"]
        vs = req.app.state.services["vector_store"]
        docs = await proc.process_file(str(tmp))
        await vs.add_documents(docs, namespace=namespace)
        return {"status": "ok", "chunks": len(docs)}
    finally:
        tmp.unlink(missing_ok=True)


@router.post("/ingest", dependencies=[Depends(verify_api_key)])
async def ingest(req: Request, source: str, namespace: Optional[str] = None):
    pipe = req.app.state.services["ingestion_pipeline"]
    return await pipe.ingest_source(source, namespace=namespace)


@router.delete("/{doc_id}", dependencies=[Depends(verify_api_key)])
async def delete(req: Request, doc_id: str, namespace: Optional[str] = None):
    await req.app.state.services["vector_store"].delete_documents([doc_id], namespace=namespace)
    return {"status": "deleted"}
