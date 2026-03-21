"""FHIR API client for the Annuaire Sante."""

import httpx

from annuaire_mcp.categories import build_type_token
from annuaire_mcp.config import Settings
from annuaire_mcp.models import Address, Establishment, SearchResult, Telecom


def _parse_establishment(resource: dict) -> Establishment:
    """Parse a FHIR Organization resource into an Establishment.

    Args:
        resource: A raw FHIR Organization resource as a dict.

    Returns:
        An Establishment instance populated from the resource.
    """
    finess_id: str | None = None
    for identifier in resource.get("identifier", []):
        system = identifier.get("system", "")
        if "finess" in system.lower():
            finess_id = identifier.get("value")
            break

    _CATEGORY_SYSTEM = (
        "https://mos.esante.gouv.fr/NOS/TRE_R66-CategorieEtablissement"
        "/FHIR/TRE-R66-CategorieEtablissement"
    )
    category_code: str | None = None
    category_label: str | None = None
    for type_entry in resource.get("type", []):
        for coding in type_entry.get("coding", []):
            if coding.get("system") == _CATEGORY_SYSTEM:
                category_code = coding.get("code")
                category_label = coding.get("display")
                break
        if category_code is not None:
            break

    raw_address = resource.get("address", [{}])[0] if resource.get("address") else {}
    address = Address(
        line=raw_address.get("line", []),
        city=raw_address.get("city"),
        postal_code=raw_address.get("postalCode"),
        country=raw_address.get("country"),
    )

    telecoms = [
        Telecom(
            system=t.get("system"),
            value=t.get("value"),
            use=t.get("use"),
        )
        for t in resource.get("telecom", [])
    ]

    # Extract coordinates from the FHIR extension if present
    latitude: float | None = None
    longitude: float | None = None
    for ext in resource.get("extension", []):
        if "geolocation" in ext.get("url", ""):
            for sub in ext.get("extension", []):
                if sub.get("url") == "latitude":
                    latitude = sub.get("valueDecimal")
                elif sub.get("url") == "longitude":
                    longitude = sub.get("valueDecimal")

    return Establishment(
        finess_id=finess_id,
        name=resource.get("name"),
        category_code=category_code,
        category_label=category_label,
        active=resource.get("active"),
        address=address,
        telecoms=telecoms,
        latitude=latitude,
        longitude=longitude,
    )


class FhirClient:
    """Async HTTP client for the Annuaire Sante FHIR v2 API.

    Args:
        settings: Application settings containing the API key and base URL.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._http = httpx.AsyncClient(
            base_url=settings.fhir_base_url,
            headers={
                "ESANTE-API-KEY": settings.esante_api_key,
                "Accept": "application/fhir+json",
            },
            timeout=settings.http_timeout,
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def search_organizations(
        self,
        postal_code: str,
        category_code: str,
        max_results: int | None = None,
        active_only: bool = True,
    ) -> SearchResult:
        """Search for health establishments by postal code prefix.

        The ANS FHIR v2 API does not support geographic (_near) search on
        Organisation resources. Geographic filtering is approximated by
        searching on ``address-postalcode`` (prefix match).

        Args:
            postal_code: Postal code or prefix to search within
                         (e.g. "75014" for one arrondissement, "75" for all Paris).
            category_code: FINESS category code (e.g. "500" for EHPAD).
            max_results: Maximum number of results to return.
            active_only: If True, only return active establishments.

        Returns:
            A SearchResult containing the matching establishments.

        Raises:
            httpx.HTTPStatusError: If the API returns a non-2xx status.
        """
        count = max_results or self._settings.max_results
        params: dict[str, str | int] = {
            "address-postalcode": postal_code,
            "type": build_type_token(category_code),
            "_count": count,
        }
        if active_only:
            params["active"] = "true"

        response = await self._http.get("/Organization", params=params)
        response.raise_for_status()

        bundle = response.json()
        entries = bundle.get("entry", [])
        establishments = [
            _parse_establishment(entry["resource"])
            for entry in entries
            if "resource" in entry
        ]

        return SearchResult(
            total=bundle.get("total"),
            count=len(establishments),
            establishments=establishments,
        )

    async def get_organization_by_finess(self, finess_id: str) -> Establishment | None:
        """Retrieve a single establishment by its FINESS identifier.

        Args:
            finess_id: The FINESS geographic entity number.

        Returns:
            An Establishment, or None if not found.

        Raises:
            httpx.HTTPStatusError: If the API returns a non-2xx status.
        """
        params = {
            "identifier": f"https://finess.esante.gouv.fr|{finess_id}",
            "_count": 1,
        }
        response = await self._http.get("/Organization", params=params)
        response.raise_for_status()

        bundle = response.json()
        entries = bundle.get("entry", [])
        if not entries:
            return None

        return _parse_establishment(entries[0]["resource"])
