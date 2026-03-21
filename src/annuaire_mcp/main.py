"""Entry point for the Annuaire Sante MCP server."""

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
    """Start the MCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    run()
