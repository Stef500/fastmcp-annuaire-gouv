"""Nominatim geocoding client for the Annuaire Sante server."""

import logging

import httpx

logger = logging.getLogger(__name__)

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
_NOMINATIM_HEADERS = {
    "User-Agent": (
        "fastmcp-annuaire-gouv/1.0 "
        "(https://github.com/Stef500/fastmcp-annuaire-gouv)"
    )
}
_NOMINATIM_TIMEOUT = 10.0

class NominatimClient:
    """Async HTTP client for the Nominatim geocoding API.

    Uses a persistent connection pool (rather than per-call AsyncClient) and
    an in-process cache for reverse geocoding results.
    """

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(
            headers=_NOMINATIM_HEADERS,
            timeout=_NOMINATIM_TIMEOUT,
        )
        # In-process cache: (lat, lon) rounded to 4 dp → postal code.
        # Eliminates repeated Nominatim round-trips for identical coordinates.
        self._reverse_cache: dict[tuple[float, float], str | None] = {}

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def reverse_geocode_postal(
        self, latitude: float, longitude: float
    ) -> str | None:
        """Return the French postal code for a GPS point.

        Results are cached in-process keyed on coordinates rounded to 4 decimal
        places (~11 m precision), avoiding redundant Nominatim calls.

        Args:
            latitude: WGS-84 latitude.
            longitude: WGS-84 longitude.

        Returns:
            A 5-digit French postal code, or None if not found.

        Raises:
            ValueError: On network errors or non-2xx HTTP responses.
        """
        cache_key = (round(latitude, 4), round(longitude, 4))
        if cache_key in self._reverse_cache:
            logger.debug("Reverse geocode cache hit for %s", cache_key)
            return self._reverse_cache[cache_key]

        try:
            response = await self._http.get(
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

        postal_code = data.get("address", {}).get("postcode")
        self._reverse_cache[cache_key] = postal_code
        return postal_code

    async def geocode_address(self, address: str) -> dict:
        """Convert a French address or place name to GPS coordinates.

        Args:
            address: Free-text address or place name.

        Returns:
            A dict with ``latitude``, ``longitude``, and ``display_name``,
            or a dict with an ``error`` key on failure.
        """
        try:
            response = await self._http.get(
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
            return {
                "error": f"Geocoding service returned HTTP {exc.response.status_code}."
            }
        except httpx.RequestError:
            return {"error": "Geocoding service is unavailable. Please try again later."}

        if not results:
            return {}

        hit = results[0]
        return {
            "latitude": float(hit["lat"]),
            "longitude": float(hit["lon"]),
            "display_name": hit.get("display_name"),
        }
