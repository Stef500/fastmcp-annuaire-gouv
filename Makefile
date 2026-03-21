.DEFAULT_GOAL := help

.PHONY: help install test lint format check run docker docker-ghcr audit clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

install: ## Install dependencies and activate pre-commit hooks
	uv sync
	uv run pre-commit install

test: ## Run the test suite with coverage
	uv run pytest tests/ -v

lint: ## Lint with ruff (auto-fix) and check formatting with black
	uv run ruff check --fix src/ tests/
	uv run black --check src/ tests/

format: ## Auto-format with black
	uv run black src/ tests/

check: ## Run all CI checks (lint + format + tests + audit)
	uv run ruff check src/ tests/
	uv run black --check src/ tests/
	uv run pytest tests/ -v
	uvx pip-audit

run: ## Start the MCP server (stdio transport)
	uv run python -m annuaire_mcp.main

docker: ## Build and run with docker compose (local image)
	docker compose up --build

docker-ghcr: ## Pull and run the published image from ghcr.io
	docker compose -f docker-compose.ghcr.yml pull
	docker compose -f docker-compose.ghcr.yml up

audit: ## Check dependencies for known vulnerabilities
	uvx pip-audit

clean: ## Remove build artefacts and cache directories
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
	find . -type f -name '*.pyc' -not -path './.venv/*' -delete
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage coverage.xml build dist
