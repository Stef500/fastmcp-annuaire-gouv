# Deployment

## Docker (recommended)

### Prerequisites

- Docker and Docker Compose installed
- An Annuaire Sante API key

### Option 1 — Build locally

Uses `docker-compose.yml`, builds the image from source:

```bash
cp .env.example .env
# Edit .env: set ESANTE_API_KEY=<your_key>

docker compose up --build
```

### Option 2 — Use the published image (no build required)

Uses `docker-compose.ghcr.yml`, pulls the pre-built image from `ghcr.io`:

```bash
cp .env.example .env
# Edit .env: set ESANTE_API_KEY=<your_key>

docker compose -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.ghcr.yml up
```

The container starts the MCP server and listens on stdio.
The `stdin_open: true` and `tty: true` settings are required for the stdio transport.

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ESANTE_API_KEY` | yes | - | ANS FHIR API key |
| `FHIR_BASE_URL` | no | `https://gateway.api.esante.gouv.fr/fhir/v2` | Override the FHIR base URL |
| `HTTP_TIMEOUT` | no | `30` | Request timeout in seconds |
| `MAX_RESULTS` | no | `50` | Maximum results per query |
| `MCP_TRANSPORT` | no | `stdio` | Transport mode: `stdio` or `http` |
| `MCP_HOST` | no | `127.0.0.1` | Bind address (http transport only) |
| `MCP_PORT` | no | `8000` | Bind port (http transport only) |
| `LOG_LEVEL` | no | `WARNING` | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Using the published image

The image is automatically published to GitHub Container Registry on every push
to `main`:

```
ghcr.io/stef500/fastmcp-annuaire-gouv:latest
ghcr.io/stef500/fastmcp-annuaire-gouv:sha-<commit-sha>
```

#### Local usage

Pull and run the image directly (requires a `.env` file with `ESANTE_API_KEY`):

```bash
docker pull ghcr.io/stef500/fastmcp-annuaire-gouv:latest
docker run -i --rm --env-file .env ghcr.io/stef500/fastmcp-annuaire-gouv:latest
```

#### Remote / server usage

On a remote machine, pull and run with the env variable passed inline:

```bash
docker pull ghcr.io/stef500/fastmcp-annuaire-gouv:latest
docker run -i --rm \
  -e ESANTE_API_KEY=<your_key> \
  ghcr.io/stef500/fastmcp-annuaire-gouv:latest
```

Or with docker compose using the provided `docker-compose.ghcr.yml`:

```bash
# Pull the latest image and start
docker compose -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.ghcr.yml up
```

## Health check (HTTP transport)

When running with `MCP_TRANSPORT=http`, a `GET /health` endpoint is available:

```bash
curl http://localhost:8000/health
# {"status": "ok", "service": "annuaire-sante"}
```

The Docker image includes a `HEALTHCHECK` directive that polls this endpoint automatically.
For stdio transport (default), the health check directive has no effect and can be ignored.

## GitHub Actions — automated build and push

The workflow in `.github/workflows/docker-publish.yml` runs on every push to
`main`. It:

1. Runs the test suite (pytest + ruff + black checks) and audits dependencies with `pip-audit`.
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
        "ghcr.io/stef500/fastmcp-annuaire-gouv:latest"
      ]
    }
  }
}
```
