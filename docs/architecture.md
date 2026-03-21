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
3. `tools.py` reverse-geocodes the coordinates to a French postal code via Nominatim.
4. The postal code is shortened to a department prefix when `radius_km > 10`.
5. `client.py` sends `GET /Organization?address-postalcode=<code>&type=<token>` to the ANS FHIR v2 API.
   If the result is empty and a precise postal code was used, a second request widens the scope to the department prefix.
6. The FHIR bundle is parsed: each `Organization` resource becomes an `Establishment`.
   The category code is extracted from the `TRE_R66-CategorieEtablissement` type entry (the `type[]` array may contain several entries with different systems).
7. A `SearchResult` is returned to the LLM as JSON.

> **API limitation**: the ANS FHIR v2 `Organization` resource does not expose a
> `_near` (radius-based) search parameter. Geographic filtering relies on postal
> codes. See [api-reference.md](api-reference.md) for details.

## Security considerations

- The API key is never stored in code. It is read exclusively from the environment
  or `.env` file via `pydantic-settings`.
- The `.env` file is excluded from version control via `.gitignore`.
- The Docker image runs as a non-root user (`appuser`).
- HTTP timeouts are enforced to prevent indefinite blocking.
- `max_results` is capped by the server-side setting to prevent large payloads.
