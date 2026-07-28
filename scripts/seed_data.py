import asyncio
from src.services.embedding_service import EmbeddingService
from src.services.document_processor import DocumentProcessor, DocumentIngestionPipeline
from src.knowledge.vector_store import VectorStoreService
from src.config.redis import create_redis

async def main():
    r = create_redis()
    vs = VectorStoreService(EmbeddingService(r))
    pipe = DocumentIngestionPipeline(vs, DocumentProcessor())
    print(await pipe.ingest_directory("./data/corpus", namespace="seed"))

if __name__ == "__main__":
    asyncio.run(main())
