# Testing and integration

This document covers all methods for testing the MCP server locally and
integrating it with an LLM in the cloud.

## Available tools

| MCP Tool | Description |
|---|---|
| `list_establishment_categories` | Lists all supported categories (EHPAD, IME, MAS…) |
| `geocode_address` | Converts a text address to GPS coordinates (via Nominatim/OSM, no key required) |
| `search_establishments` | Searches for establishments around a GPS point by category |
| `get_establishment_by_finess` | Retrieves an establishment by its FINESS number |

**Typical flow with an address:**

```
user: "EHPAD around 10 rue de Rivoli, Paris"
       └─> geocode_address("10 rue de Rivoli, Paris")
              └─> { latitude: 48.855, longitude: 2.351 }
                     └─> search_establishments(lat, lon, radius_km=5, category="EHPAD")
                            └─> reverse geocode → postal code (e.g.: 75001)
                                   └─> GET /Organization?address-postalcode=75001&type=…|500
                                          └─> if 0 results → retry with department prefix (75)
```

The LLM automatically orchestrates these calls in a single user request.

> **Note on geolocation**: the ANS FHIR v2 API does not support radius-based search
> (`_near`). Geographic search is approximated by postal code.
> `radius_km <= 10` → exact postal code ; `radius_km > 10` → department prefix.

## Prerequisites

An ANS API key is required for real calls to the Annuaire Sante.
Unit tests (pytest) do not need one as they mock the API.

### Obtaining an API key

1. Create an account on the ANS GRAVITEE portal:
   https://portal.api.esante.gouv.fr (more information at https://ansforge.github.io/annuaire-sante-fhir-documentation/pages/guide/version-2/getting-started/get-api-key.html)
2. Create an application to generate a key.
3. Copy the key value.

### Configuring the .env file

```bash
cp .env.example .env
# Edit .env
ESANTE_API_KEY=your_api_key_here
```

---

## Local testing

### Unit tests (without API key)

Tests mock all HTTP requests. No real key is needed.

```bash
ESANTE_API_KEY=dummy uv run pytest tests/ -v
```

To run only a specific test module:

```bash
ESANTE_API_KEY=dummy uv run pytest tests/test_client.py -v
```

---

### Direct tool call from the terminal

The fastest method to verify that a tool works with the real API.
`fastmcp call` starts the server, calls the tool and displays the result.

```bash
# List available categories
ESANTE_API_KEY=your_api_key uv run fastmcp call \
  src/annuaire_mcp/main.py \
  --target list_establishment_categories

# Search for EHPADs around Paris within a 5 km radius
ESANTE_API_KEY=your_api_key uv run fastmcp call \
  src/annuaire_mcp/main.py \
  --target search_establishments \
  latitude=48.8566 longitude=2.3522 radius_km=5 category=EHPAD max_results=5

# Other category examples
ESANTE_API_KEY=your_api_key uv run fastmcp call \
  src/annuaire_mcp/main.py \
  --target search_establishments \
  latitude=45.7640 longitude=4.8357 radius_km=10 category=IME

# Geocode an address (no ANS API key needed, Nominatim is public)
ESANTE_API_KEY=your_api_key uv run fastmcp call \
  src/annuaire_mcp/main.py \
  --target geocode_address \
  address="14 rue de la Paix, Paris"

# Search for an establishment by its FINESS number
ESANTE_API_KEY=your_api_key uv run fastmcp call \
  src/annuaire_mcp/main.py \
  --target get_establishment_by_finess \
  finess_id=750123456
```

To get the response as raw JSON (useful for debugging or scripting):

```bash
ESANTE_API_KEY=your_api_key uv run fastmcp call \
  src/annuaire_mcp/main.py \
  --target search_establishments \
  --json \
  latitude=48.8566 longitude=2.3522 radius_km=5 category=EHPAD
```

---

### Interactive MCP Inspector

FastMCP includes the MCP Inspector, a web interface for exploring tools,
visualizing their JSON schemas and calling them manually.

```bash
ESANTE_API_KEY=your_api_key uv run fastmcp dev inspector src/annuaire_mcp/main.py
```

The URL `http://localhost:6274` opens automatically in the browser.
It provides:

- the list of tools with their parameter schemas
- a form to call each tool
- the raw and formatted response

**Alternative: HTTP transport + Inspector**

If you are running the server in HTTP mode, use `make inspect` instead:

```bash
# Terminal 1
make run-http

# Terminal 2
make inspect   # opens the Inspector against http://localhost:8000/mcp
```

---

### Via Docker locally

```bash
docker compose up --build
```

To send a command to the container from another terminal:

```bash
docker run -it --rm --env-file .env annuaire-mcp:latest
```

---

## Integration with an LLM in the cloud

### Case A — Claude Desktop (local client, remote model)

Claude Desktop runs on your machine and connects to the Claude model via
the Anthropic API. The MCP server also runs locally via stdio. This is the
simplest method for everyday use.

**Automatic installation:**

```bash
ESANTE_API_KEY=your_api_key uv run fastmcp install claude-desktop \
  src/annuaire_mcp/main.py \
  --name "annuaire-sante"
```

**Manual installation:**

Edit the Claude Desktop configuration file:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

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

Restart Claude Desktop. The server appears in the tools list (hammer icon).
Example queries:

> "Find all EHPADs within a 10 km radius around Lyon."
>
> "Which IMEs are located less than 20 km from Bordeaux (44.8378, -0.5792)?"
>
> "Give me the information for establishment FINESS 750123456."

---

### Case B — Claude Code

```bash
ESANTE_API_KEY=your_api_key uv run fastmcp install claude-code \
  src/annuaire_mcp/main.py \
  --name "annuaire-sante"
```

Or from Claude Code, use the `/mcp` command to add the server
manually with the stdio configuration.

---

### Case C — Cursor

```bash
ESANTE_API_KEY=your_api_key uv run fastmcp install cursor \
  src/annuaire_mcp/main.py \
  --name "annuaire-sante"
```

---

### Case D — LM Studio (local LLM)

LM Studio allows running an LLM locally (Llama, Mistral, Qwen, etc.)
and exposes an OpenAI-compatible API. Recent versions support the
MCP protocol via stdio, which allows connecting the server directly.

#### Step 1 — Install LM Studio

Download LM Studio from https://lmstudio.ai and install it.
Choose a model with a sufficiently large context window (recommended:
32k tokens minimum) and good tool use capabilities,
for example:

- `Qwen2.5-72B-Instruct` (GGUF Q4)
- `Mistral-Small-3.1-24B-Instruct-2503` (GGUF Q4)
- `Meta-Llama-3.3-70B-Instruct` (GGUF Q4)

#### Step 2 — Enable MCP support in LM Studio

In LM Studio:

1. Go to **Settings > Developer**.
2. Enable **"Enable MCP support"**.
3. Click **"Edit MCP config"** — this opens a JSON file.

#### Step 3 — Add the MCP server

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

Replace `/absolute/path/to/fastmcp-annuaire-gouv` with the actual path,
for example `/home/alice/fastmcp-annuaire-gouv`.

#### Step 4 — Test

Restart LM Studio. In the chat, select the loaded model then ask
a question that requires the tools:

> "Find me EHPADs within 5 km of Paris (48.8566, 2.3522)."

The model should automatically call `search_establishments` and display
the results.

#### Tips

- Some models do not handle tool use well with complex schemas.
  If the model does not call the tools, try a larger model or one that is
  better instruction-tuned.
- LM Studio 0.3.x and above is required for MCP support.
- Monitor the logs under **Developer > MCP logs** if there are connection
  issues with the server.

---

### Case E — Claude.ai cloud via HTTP

Claude.ai (Pro or Team subscription) can connect to a remote MCP server
via HTTP. This requires exposing the server on a public URL.

#### Step 1 — Enable HTTP transport

Modify `src/annuaire_mcp/main.py` to support both transports:

```python
import os

def run() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))

    if transport == "http":
        mcp.run(transport="http", host=host, port=port)
    else:
        mcp.run()
```

Add to `.env`:

```bash
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=8000
```

Start the server:

```bash
uv run python -m annuaire_mcp.main
```

#### Step 2 — Expose the server publicly (for development)

With Cloudflare Tunnel (free, no account required):

```bash
cloudflared tunnel --url http://localhost:8000
# Returns a URL such as: https://abc123.trycloudflare.com
```

With ngrok:

```bash
ngrok http 8000
# Returns a URL such as: https://abc123.ngrok-free.app
```

#### Step 3 — Add the server in Claude.ai

- Go to Settings > Integrations > Add an MCP server
- URL: `https://abc123.trycloudflare.com/mcp/`

#### Production deployment with Docker

For a permanent setup, run the container with HTTP transport and
place a reverse proxy (Caddy, Traefik, nginx) in front of it.

Example with Caddy (`Caddyfile`):

```
mcp.mondomaine.fr {
    reverse_proxy annuaire-mcp:8000
}
```

Adapted `docker-compose.yml`:

```yaml
services:
  annuaire-mcp:
    image: ghcr.io/stef500/fastmcp-annuaire-gouv:latest
    env_file: .env
    environment:
      MCP_TRANSPORT: http
      MCP_HOST: 0.0.0.0
      MCP_PORT: "8000"
    expose:
      - "8000"

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data

volumes:
  caddy_data:
```

---

## Methods summary

| Method | Real API key | Complexity | Use case |
|---|---|---|---|
| `pytest` | No | Minimal | CI, TDD, regression |
| `fastmcp call` | Yes | Minimal | Quick smoke test in CLI |
| `fastmcp dev inspector` | Yes | Low | Interactive debugging, exploration |
| Claude Desktop (stdio) | Yes | Low | Daily use with Claude |
| Claude Code | Yes | Low | Terminal use |
| LM Studio (local stdio) | Yes | Low | Open-source LLM locally |
| Claude.ai + HTTP tunnel | Yes | Medium | Demo, testing from the cloud |
| Docker + reverse proxy | Yes | High | Production |
