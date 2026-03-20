# Architecture

## Overview

```
LLM / MCP client (Claude Desktop, etc.)
        |  stdio (MCP protocol)
        v
  annuaire_mcp.main     <- FastMCP server entry point
        |
  annuaire_mcp.tools    <- MCP tool definitions
        |
  annuaire_mcp.client   <- Async FHIR HTTP client (httpx)
        |
  annuaire_mcp.models   <- Pydantic domain models
  annuaire_mcp.categories <- FINESS code registry
  annuaire_mcp.config   <- Settings (pydantic-settings, .env)
        |
  Annuaire Sante FHIR v2 API (gateway.api.esante.gouv.fr)
```

## Modules

| Module | Responsibility |
|---|---|
| `main.py` | Creates the `FastMCP` instance, registers tools, defines the `run()` entry point |
| `tools.py` | Declares the three MCP tools exposed to the LLM |
| `client.py` | Wraps `httpx.AsyncClient` to call the FHIR API, parses FHIR resources |
| `models.py` | Pydantic models (`Establishment`, `SearchResult`, `Address`, `Telecom`) |
| `categories.py` | Maps human-readable category keys to FINESS codes and builds FHIR type tokens |
| `config.py` | `pydantic-settings` `Settings` class; reads from `.env` |

## Data flow for a search request

1. The LLM calls `search_establishments(latitude, longitude, radius_km, category)`.
2. `tools.py` resolves the category key to a numeric FINESS code via `categories.py`.
3. `client.py` builds the FHIR query parameters and sends a `GET /Organization` request.
4. The FHIR bundle is parsed: each `Organization` resource becomes an `Establishment`.
5. A `SearchResult` is returned to the LLM as JSON.

## Security considerations

- The API key is never stored in code. It is read exclusively from the environment
  or `.env` file via `pydantic-settings`.
- The `.env` file is excluded from version control via `.gitignore`.
- The Docker image runs as a non-root user (`appuser`).
- HTTP timeouts are enforced to prevent indefinite blocking.
- `max_results` is capped by the server-side setting to prevent large payloads.
