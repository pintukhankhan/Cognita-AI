from __future__ import annotations
import asyncio, csv, hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
import structlog
import httpx
from src.utils.helpers import new_id

logger = structlog.get_logger(__name__)


class RecursiveSplitter:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200,
                 separators: tuple = ("\n\n", "\n", ". ", " ")):
        self.chunk_size, self.overlap, self.seps = chunk_size, overlap, separators

    def split(self, text: str) -> List[str]:
        return self._split(text, 0)

    def _split(self, text: str, level: int) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []
        if level >= len(self.seps):
            return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size - self.overlap)]
        sep = self.seps[level]
        parts = text.split(sep)
        chunks, buf = [], ""
        for p in parts:
            piece = p if not buf else buf + sep + p
            if len(piece) <= self.chunk_size:
                buf = piece
            else:
                if buf:
                    chunks.append(buf)
                if len(p) > self.chunk_size:
                    chunks.extend(self._split(p, level + 1))
                    buf = ""
                else:
                    buf = p
        if buf:
            chunks.append(buf)
        out = []
        for i, c in enumerate(chunks):
            if i and self.overlap:
                c = chunks[i - 1][-self.overlap:] + c
            out.append(c)
        return [c for c in out if c.strip()]


class DocumentProcessor:
    EXT = {".pdf", ".txt", ".docx", ".doc", ".csv"}

    def __init__(self):
        self.splitter = RecursiveSplitter()

    async def process_file(self, path: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)
        text = await asyncio.to_thread(self._load, p)
        chunks = self.splitter.split(text)
        fhash = hashlib.sha256(p.read_bytes()).hexdigest()
        docs = []
        for i, c in enumerate(chunks):
            docs.append({"id": f"{p.stem}_{i}_{new_id()[:8]}", "text": c,
                         "metadata": {**(metadata or {}), "source": str(p), "chunk_index": i,
                                      "total_chunks": len(chunks), "file_hash": fhash}})
        logger.info("cognita.doc.processed", file=str(p), chunks=len(docs))
        return docs

    def _load(self, p: Path) -> str:
        ext = p.suffix.lower()
        if ext == ".txt":
            return p.read_text(encoding="utf-8", errors="ignore")
        if ext == ".pdf":
            from pypdf import PdfReader
            return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
        if ext in (".docx", ".doc"):
            from docx import Document
            return "\n".join(par.text for par in Document(str(p)).paragraphs)
        if ext == ".csv":
            with p.open(encoding="utf-8", errors="ignore") as f:
                return "\n".join(",".join(row) for row in csv.reader(f))
        raise ValueError(f"Unsupported: {ext}")

    async def fetch_url(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(url); r.raise_for_status()
            tmp = Path("/tmp") / f"{new_id()}.txt"; tmp.write_bytes(r.content)
            return str(tmp)


class DocumentIngestionPipeline:
    def __init__(self, vector_store, processor: DocumentProcessor):
        self.vs = vector_store
        self.proc = processor
        self._tasks: Dict[str, str] = {}

    async def ingest_directory(self, directory: str, namespace: Optional[str] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        files = [f for f in Path(directory).rglob("*")
                 if f.is_file() and f.suffix.lower() in DocumentProcessor.EXT]
        ok = fail = chunks = 0
        errs: List[Dict[str, str]] = []
        for f in files:
            try:
                docs = await self.proc.process_file(str(f), metadata)
                await self.vs.add_documents(docs, namespace=namespace)
                ok += 1; chunks += len(docs)
            except Exception as e:
                fail += 1; errs.append({"file": str(f), "error": str(e)})
        return {"total_files": len(files), "successful": ok, "failed": fail,
                "total_chunks": chunks, "errors": errs}

    async def ingest_source(self, source: str, namespace: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if source.startswith(("http://", "https://")):
            local = await self.proc.fetch_url(source)
            docs = await self.proc.process_file(local, metadata)
        elif Path(source).is_dir():
            return await self.ingest_directory(source, namespace, metadata)
        else:
            docs = await self.proc.process_file(source, metadata)
        await self.vs.add_documents(docs, namespace=namespace)
        return {"chunks": len(docs)}

    async def schedule_reindex(self, namespace: Optional[str] = None) -> str:
        task_id = new_id("reindex_")
        self._tasks[task_id] = "running"

        async def _run():
            try:
                await self.vs.delete_all(namespace=namespace)
                self._tasks[task_id] = "done"
            except Exception as e:
                self._tasks[task_id] = f"error:{e}"

        asyncio.create_task(_run())
        return task_id
