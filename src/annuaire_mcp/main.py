"""Entry point for the Annuaire Sante MCP server."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from annuaire_mcp.client import FhirClient
from annuaire_mcp.config import get_settings
from annuaire_mcp.geocoder import NominatimClient
from annuaire_mcp.tools import register_tools

_settings = get_settings()
_fhir_client = FhirClient(_settings)
_nominatim_client = NominatimClient()


@asynccontextmanager
async def _lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Gracefully close HTTP clients on server shutdown."""
    yield
    await _fhir_client.close()
    await _nominatim_client.close()


mcp = FastMCP(
    name="annuaire-sante",
    lifespan=_lifespan,
    instructions=(
        "This server provides tools to query the French Annuaire Sante FHIR API. "
        "You can search for health and medico-social establishments (EHPAD, IME, MAS, "
        "EEAP, SSIAD, ...) by geographic area. "
        "Start with 'list_establishment_categories' to see available types, then use "
        "'search_establishments' with coordinates and a radius."
    ),
)

register_tools(mcp, _fhir_client, _nominatim_client)


def run() -> None:
    """Start the MCP server.

    Transport is controlled by the ``MCP_TRANSPORT`` environment variable:
    - ``stdio`` (default): standard MCP transport for local clients.
    - ``http``: HTTP transport for remote clients (e.g. Claude.ai cloud).
      Reads ``MCP_HOST`` (default ``127.0.0.1``) and ``MCP_PORT`` (default ``8000``).

    Log verbosity is controlled by the ``LOG_LEVEL`` environment variable
    (default: ``WARNING``).
    """
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "WARNING").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "http":
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_PORT", "8000"))
        mcp.run(transport="http", host=host, port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    run()
