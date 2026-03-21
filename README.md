# fastmcp-annuaire-gouv

MCP server for querying the French Annuaire Sante FHIR API in real-time.

Allows an LLM to find health and medico-social establishments (EHPAD, IME, MAS, EEAP,
SSIAD, ...) of a specific category within a defined geographic radius.

## Documentation

- [Getting started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [API reference](docs/api-reference.md)
- [Deployment](docs/deployment.md)
- [Tests et integration LLM](docs/testing-and-integration.md)

## Quick start

```bash
cp .env.example .env
# Edit .env and set ESANTE_API_KEY

uv sync
uv run python -m annuaire_mcp.main
```

## Docker

Build and run locally:

```bash
docker compose up --build
```

Or use the published image from ghcr.io (no build required):

```bash
docker compose -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.ghcr.yml up
```

See [Deployment](docs/deployment.md) for full local and remote usage details.

## Tests

```bash
uv run pytest tests/ -v
```
