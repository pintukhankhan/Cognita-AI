import asyncio
from neo4j import AsyncGraphDatabase
from src.config.settings import settings

STMTS = [
    "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
    "CREATE FULLTEXT INDEX entityIndex IF NOT EXISTS FOR (e:Entity) ON EACH [e.name]",
]

async def main():
    d = AsyncGraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
    async with d.session() as s:
        for q in STMTS:
            print("→", q[:60]); await s.run(q)
    await d.close(); print("✅ Cognita migrations done")

if __name__ == "__main__":
    asyncio.run(main())
