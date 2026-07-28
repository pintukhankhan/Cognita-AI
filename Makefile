.PHONY: install run test lint fmt migrate seed docker clean
install:
	bash scripts/setup.sh
run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
test:
	pytest
lint:
	ruff check src tests
fmt:
	black src tests && ruff check --fix src tests
migrate:
	python scripts/migrate.py
seed:
	python scripts/seed_data.py
docker:
	docker compose -f docker/docker-compose.yml up -d --build
clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
