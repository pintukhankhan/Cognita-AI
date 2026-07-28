#!/usr/bin/env bash
set -euo pipefail
echo "🧠 Setting up Cognita..."
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt
cp -n .env.example .env || true
docker compose -f docker/docker-compose.yml up -d redis neo4j
echo "waiting for neo4j..."; until curl -fs http://localhost:7474 >/dev/null; do sleep 2; done
python scripts/migrate.py
echo "✅ Cognita ready → uvicorn src.main:app --reload"
