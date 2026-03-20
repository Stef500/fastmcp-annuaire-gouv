"""MCP tool definitions for the Annuaire Sante server."""

from fastmcp import FastMCP

from annuaire_mcp.categories import CATEGORIES, get_category_code
from annuaire_mcp.client import FhirClient
from annuaire_mcp.config import get_settings
from annuaire_mcp.models import SearchResult


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools onto the server instance.

    Args:
        mcp: The FastMCP server instance.
    """
    settings = get_settings()
    client = FhirClient(settings)

    @mcp.tool()
    def list_establishment_categories() -> dict[str, dict[str, str]]:
        """List all supported health establishment categories.

        Returns a mapping of category keys to their code and French label.
        Use the returned keys as the ``category`` parameter in
        ``search_establishments``.
        """
        return {
            key: {"code": code, "label": label}
            for key, (code, label) in CATEGORIES.items()
        }

    @mcp.tool()
    async def search_establishments(
        latitude: float,
        longitude: float,
        radius_km: float,
        category: str,
        max_results: int = 20,
        active_only: bool = True,
    ) -> SearchResult:
        """Search for health establishments near a geographic point.

        Args:
            latitude: Latitude of the center point (WGS-84 decimal degrees).
            longitude: Longitude of the center point (WGS-84 decimal degrees).
            radius_km: Search radius in kilometres (e.g. 10).
            category: Establishment category key, e.g. "EHPAD", "IME", "MAS".
                      Use ``list_establishment_categories`` to see all options.
            max_results: Maximum number of results to return (default 20, max 50).
            active_only: If True (default), only return active establishments.

        Returns:
            A SearchResult with the matching establishments and their details.

        Raises:
            ValueError: If the category is not recognised.
        """
        code = get_category_code(category)
        if code is None:
            valid = ", ".join(CATEGORIES.keys())
            raise ValueError(f"Unknown category '{category}'. Valid values: {valid}")

        bounded = min(max_results, settings.max_results)
        return await client.search_organizations(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            category_code=code,
            max_results=bounded,
            active_only=active_only,
        )

    @mcp.tool()
    async def get_establishment_by_finess(finess_id: str) -> dict:
        """Retrieve a single health establishment by its FINESS number.

        Args:
            finess_id: The 9-digit FINESS geographic entity identifier.

        Returns:
            A dict representing the establishment, or an error message if
            not found.
        """
        result = await client.get_organization_by_finess(finess_id)
        if result is None:
            return {"error": f"No establishment found for FINESS id '{finess_id}'."}
        return result.model_dump(exclude_none=True)
