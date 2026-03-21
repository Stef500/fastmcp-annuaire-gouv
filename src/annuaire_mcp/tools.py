"""MCP tool definitions for the Annuaire Sante server."""

import logging
import re

import httpx
from fastmcp import FastMCP

from annuaire_mcp.categories import CATEGORIES, get_category_code
from annuaire_mcp.client import FhirClient
from annuaire_mcp.config import get_settings
from annuaire_mcp.models import SearchResult

logger = logging.getLogger(__name__)

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
_NOMINATIM_HEADERS = {"User-Agent": "fastmcp-annuaire-gouv/1.0"}
_NOMINATIM_TIMEOUT = 10.0

_DEPT_RADIUS_THRESHOLD_KM = 10.0

_FINESS_RE = re.compile(r"^\d{9}$")

_ADDRESS_MAX_LEN = 500


async def _reverse_geocode_postal(latitude: float, longitude: float) -> str | None:
    """Return the French postal code for a GPS point using Nominatim reverse geocoding."""
    try:
        async with httpx.AsyncClient(
            headers=_NOMINATIM_HEADERS, timeout=_NOMINATIM_TIMEOUT
        ) as http:
            response = await http.get(
                _NOMINATIM_REVERSE_URL,
                params={"lat": latitude, "lon": longitude, "format": "json"},
            )
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise ValueError("Geocoding service timed out. Please try again.") from exc
    except httpx.HTTPStatusError as exc:
        raise ValueError(
            f"Geocoding service returned HTTP {exc.response.status_code}."
        ) from exc
    except httpx.RequestError as exc:
        raise ValueError(
            "Geocoding service is unavailable. Please try again later."
        ) from exc
    return data.get("address", {}).get("postcode")


def _postal_search_prefix(postal_code: str, radius_km: float) -> str:
    """Return the postal code prefix to use for the ANS API search.

    - radius_km <= _DEPT_RADIUS_THRESHOLD_KM : exact 5-digit code (commune / arrondissement)
    - radius_km >  _DEPT_RADIUS_THRESHOLD_KM : department prefix — 3 digits for DOM/TOM (97x/98x),
                        2 digits for mainland France
    """
    if radius_km <= _DEPT_RADIUS_THRESHOLD_KM:
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
        if len(address) > _ADDRESS_MAX_LEN:
            return {"error": f"Address is too long (max {_ADDRESS_MAX_LEN} characters)."}

        try:
            async with httpx.AsyncClient(
                headers=_NOMINATIM_HEADERS, timeout=_NOMINATIM_TIMEOUT
            ) as http:
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
        except httpx.TimeoutException:
            return {"error": "Geocoding service timed out. Please try again."}
        except httpx.HTTPStatusError as exc:
            return {"error": f"Geocoding service returned HTTP {exc.response.status_code}."}
        except httpx.RequestError:
            return {"error": "Geocoding service is unavailable. Please try again later."}

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
                logger.info(
                    "No results for postal code %s; widening search to department %s",
                    search_code,
                    dept_code,
                )
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
        if not _FINESS_RE.match(finess_id):
            return {
                "error": f"Invalid FINESS id '{finess_id}'. Expected exactly 9 digits."
            }
        result = await client.get_organization_by_finess(finess_id)
        if result is None:
            return {"error": f"No establishment found for FINESS id '{finess_id}'."}
        return result.model_dump(exclude_none=True)
