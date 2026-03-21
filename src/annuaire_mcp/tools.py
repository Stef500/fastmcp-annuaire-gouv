"""MCP tool definitions for the Annuaire Sante server."""

import httpx
from fastmcp import FastMCP

from annuaire_mcp.categories import CATEGORIES, get_category_code
from annuaire_mcp.client import FhirClient
from annuaire_mcp.config import get_settings
from annuaire_mcp.models import SearchResult

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
_NOMINATIM_HEADERS = {"User-Agent": "fastmcp-annuaire-gouv/1.0"}


async def _reverse_geocode_postal(latitude: float, longitude: float) -> str | None:
    """Return the French postal code for a GPS point using Nominatim reverse geocoding."""
    async with httpx.AsyncClient(headers=_NOMINATIM_HEADERS, timeout=10) as http:
        response = await http.get(
            _NOMINATIM_REVERSE_URL,
            params={"lat": latitude, "lon": longitude, "format": "json"},
        )
        response.raise_for_status()
        data = response.json()
    return data.get("address", {}).get("postcode")


def _postal_search_prefix(postal_code: str, radius_km: float) -> str:
    """Return the postal code prefix to use for the ANS API search.

    - radius_km <= 10 : exact 5-digit code (commune / arrondissement)
    - radius_km >  10 : department prefix — 3 digits for DOM/TOM (97x/98x),
                        2 digits for mainland France
    """
    if radius_km <= 10:
        return postal_code
    if postal_code.startswith(("97", "98")):
        return postal_code[:3]
    return postal_code[:2]


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
    async def geocode_address(address: str) -> dict:
        """Convert a French address or place name to GPS coordinates.

        Uses the Nominatim geocoding service (OpenStreetMap). No API key required.
        Call this tool first when the user provides an address instead of
        latitude/longitude, then pass the returned coordinates to
        ``search_establishments``.

        Args:
            address: Free-text address or place name, e.g.
                     "14 rue de la Paix, Paris" or "Lyon".

        Returns:
            A dict with ``latitude``, ``longitude``, and ``display_name``.
            If no result is found, returns a dict with an ``error`` key.
        """
        async with httpx.AsyncClient(headers=_NOMINATIM_HEADERS, timeout=10) as http:
            response = await http.get(
                _NOMINATIM_URL,
                params={
                    "q": address,
                    "format": "json",
                    "limit": 1,
                    "countrycodes": "fr",
                },
            )
            response.raise_for_status()
            results = response.json()

        if not results:
            return {"error": f"No location found for '{address}'."}

        hit = results[0]
        return {
            "latitude": float(hit["lat"]),
            "longitude": float(hit["lon"]),
            "display_name": hit.get("display_name"),
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

        The ANS FHIR v2 API does not support radius-based geographic search.
        Geographic filtering is approximated by postal code:

        - radius_km <= 10 : establishments in the same commune / arrondissement
        - radius_km >  10 : establishments in the same department (broader)

        Args:
            latitude: Latitude of the center point (WGS-84 decimal degrees).
            longitude: Longitude of the center point (WGS-84 decimal degrees).
            radius_km: Approximate search radius. Controls granularity:
                       <= 10 km → exact postal code, > 10 km → department.
            category: Establishment category key, e.g. "EHPAD", "IME", "MAS".
                      Use ``list_establishment_categories`` to see all options.
            max_results: Maximum number of results to return (default 20, max 50).
            active_only: If True (default), only return active establishments.

        Returns:
            A SearchResult with the matching establishments and their details.

        Raises:
            ValueError: If the category is not recognised or coordinates cannot
                        be reverse-geocoded to a postal code.
        """
        code = get_category_code(category)
        if code is None:
            valid = ", ".join(CATEGORIES.keys())
            raise ValueError(f"Unknown category '{category}'. Valid values: {valid}")

        postal_code = await _reverse_geocode_postal(latitude, longitude)
        if postal_code is None:
            raise ValueError(
                "Could not determine the postal code for the given coordinates. "
                "Verify that latitude and longitude are within France."
            )

        search_code = _postal_search_prefix(postal_code, radius_km)
        bounded = min(max_results, settings.max_results)
        result = await client.search_organizations(
            postal_code=search_code,
            category_code=code,
            max_results=bounded,
            active_only=active_only,
        )
        # If no results with the precise code, widen to the department prefix.
        if result.count == 0 and len(search_code) > 2:
            dept_code = (
                postal_code[:3]
                if postal_code.startswith(("97", "98"))
                else postal_code[:2]
            )
            if dept_code != search_code:
                result = await client.search_organizations(
                    postal_code=dept_code,
                    category_code=code,
                    max_results=bounded,
                    active_only=active_only,
                )
        return result

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
