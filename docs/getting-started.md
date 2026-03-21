# Getting started

## Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- An Annuaire Sante FHIR API key (see below)

## Obtain an API key

1. Create an account on the ANS API portal: https://portal.api.esante.gouv.fr
2. Log in to GRAVITEE, the API management platform.
3. Create an application to generate your API key.
4. Copy the key value.

The key will be sent as the `ESANTE-API-KEY` HTTP header on every request.

## Installation

```bash
git clone <repository-url>
cd fastmcp-annuaire-gouv

cp .env.example .env
# Open .env and set ESANTE_API_KEY=<your_key>

uv sync
```

## Running locally

```bash
uv run python -m annuaire_mcp.main
```

The server communicates over stdio, which is the standard transport for MCP
clients such as Claude Desktop or the `mcp` CLI.

## Connecting with Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "annuaire-sante": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/fastmcp-annuaire-gouv",
        "run", "python", "-m", "annuaire_mcp.main"
      ],
      "env": {
        "ESANTE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Running with Docker

```bash
docker compose up --build
```

See [deployment documentation](deployment.md) for full Docker instructions.

## Running tests

```bash
uv run pytest tests/ -v
```

## Code quality

```bash
uv run ruff check src/ tests/
uv run black src/ tests/
```
