"""Entry point for the Annuaire Sante MCP server."""

from fastmcp import FastMCP

from annuaire_mcp.tools import register_tools

mcp = FastMCP(
    name="annuaire-sante",
    instructions=(
        "This server provides tools to query the French Annuaire Sante FHIR API. "
        "You can search for health and medico-social establishments (EHPAD, IME, MAS, "
        "EEAP, SSIAD, ...) by geographic area. "
        "Start with 'list_establishment_categories' to see available types, then use "
        "'search_establishments' with coordinates and a radius."
    ),
)

register_tools(mcp)


def run() -> None:
    """Start the MCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    run()
