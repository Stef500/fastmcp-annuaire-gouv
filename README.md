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

make install
make run
```

## Common commands

```bash
make test        # run tests with coverage
make check       # full CI check (lint + format + tests + audit)
make docker      # build and run with docker compose
make docker-ghcr # pull and run the published image from ghcr.io
make clean       # remove build artefacts and caches
```

See [Deployment](docs/deployment.md) for full local and remote usage details.
