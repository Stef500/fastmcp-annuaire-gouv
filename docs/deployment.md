# Deployment

## Docker (recommended)

### Prerequisites

- Docker and Docker Compose installed
- An Annuaire Sante API key

### Steps

```bash
cp .env.example .env
# Edit .env: set ESANTE_API_KEY=<your_key>

docker compose up --build
```

The container starts the MCP server and listens on stdio.
The `stdin_open: true` and `tty: true` settings in `docker-compose.yml` are
required for the stdio transport.

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ESANTE_API_KEY` | yes | - | ANS FHIR API key |
| `FHIR_BASE_URL` | no | `https://gateway.api.esante.gouv.fr/fhir/v2` | Override the FHIR base URL |
| `HTTP_TIMEOUT` | no | `30` | Request timeout in seconds |
| `MAX_RESULTS` | no | `50` | Maximum results per query |

### Using the published image

Once the GitHub Actions workflow has run, the image is published to the GitHub
Container Registry:

```bash
docker pull ghcr.io/<owner>/fastmcp-annuaire-gouv:latest
docker run -i --env-file .env ghcr.io/<owner>/fastmcp-annuaire-gouv:latest
```

## GitHub Actions — automated build and push

The workflow in `.github/workflows/docker-publish.yml` runs on every push to
`main`. It:

1. Runs the test suite (pytest + ruff + black checks).
2. Builds the Docker image using Buildx with GitHub Actions cache.
3. Pushes to GitHub Container Registry (`ghcr.io`) with two tags:
   - `latest` (always points to the last successful main build)
   - `sha-<commit-sha>` (immutable reference)

The workflow uses `GITHUB_TOKEN` (automatically provided by GitHub Actions) for
authentication; no additional secrets are needed for the image push.

## Running without Docker

```bash
uv sync
ESANTE_API_KEY=<key> uv run python -m annuaire_mcp.main
```

## Connecting an MCP client

The server communicates over stdio. Example configuration for Claude Desktop:

```json
{
  "mcpServers": {
    "annuaire-sante": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--env-file", "/absolute/path/.env",
        "ghcr.io/<owner>/fastmcp-annuaire-gouv:latest"
      ]
    }
  }
}
```
