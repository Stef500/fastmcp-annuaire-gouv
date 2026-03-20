# fastmcp-annuaire-gouv

MCP server for querying the French Annuaire Sante FHIR API in real-time.

Allows an LLM to find health and medico-social establishments (EHPAD, IME, MAS, EEAP,
SSIAD, ...) of a specific category within a defined geographic radius.

## Documentation

- [Getting started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [API reference](docs/api-reference.md)
- [Deployment](docs/deployment.md)

## Quick start

```bash
cp .env.example .env
# Edit .env and set ESANTE_API_KEY

uv sync
uv run python -m annuaire_mcp.main
```

## Docker

```bash
docker compose up --build
```

## Tests

```bash
uv run pytest tests/ -v
```
