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

make install
```

`make install` runs `uv sync` and activates the pre-commit hooks.

## Running locally

```bash
make run
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
make docker
```

See [deployment documentation](deployment.md) for full Docker instructions.

## Common commands

The repository includes a `Makefile` for the most frequent operations:

| Command | Description |
|---|---|
| `make install` | Install dependencies and activate pre-commit hooks |
| `make test` | Run the test suite with coverage |
| `make lint` | Lint with ruff (auto-fix) and check formatting |
| `make format` | Auto-format with black |
| `make check` | Full CI check: lint + format + tests + audit |
| `make run` | Start the MCP server |
| `make docker` | Build and run with docker compose |
| `make docker-ghcr` | Pull and run the published image from ghcr.io |
| `make audit` | Check dependencies for known vulnerabilities |
| `make clean` | Remove build artefacts and cache directories |

## Pre-commit hooks

The repository ships with a `pre-commit` configuration that runs `ruff` and
`black` automatically before every commit. Hooks are activated by `make install`.

If a hook modifies files, the commit is aborted; re-stage the changes and
commit again.
