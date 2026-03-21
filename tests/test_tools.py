"""Tests for search_establishments tool and geographic helper functions."""

import json

import httpx
import pytest
import respx

from annuaire_mcp.geocoder import NominatimClient, _NOMINATIM_REVERSE_URL
from annuaire_mcp.tools import _postal_search_prefix
from tests.conftest import FHIR_BUNDLE_EMPTY, FHIR_BUNDLE_ONE_ORG

_FHIR_ORG_URL = "https://gateway.api.esante.gouv.fr/fhir/v2/Organization"

_REVERSE_PARIS = {"address": {"postcode": "75004", "city": "Paris"}}
_REVERSE_NO_POSTCODE = {"address": {"city": "Somewhere"}}


# ── _postal_search_prefix ────────────────────────────────────────────────────


def test_postal_prefix_small_radius_returns_exact_code() -> None:
    assert _postal_search_prefix("75014", 5) == "75014"


def test_postal_prefix_at_threshold_returns_exact_code() -> None:
    assert _postal_search_prefix("75014", 10) == "75014"


def test_postal_prefix_large_radius_returns_department() -> None:
    assert _postal_search_prefix("75014", 11) == "75"


def test_postal_prefix_dom_small_radius_returns_exact_code() -> None:
    assert _postal_search_prefix("97130", 5) == "97130"


def test_postal_prefix_dom_large_radius_returns_3_digit_prefix() -> None:
    assert _postal_search_prefix("97130", 20) == "971"


def test_postal_prefix_98x_large_radius_returns_3_digit_prefix() -> None:
    assert _postal_search_prefix("98800", 20) == "988"


# ── _reverse_geocode_postal ──────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_reverse_geocode_postal_found() -> None:
    respx.get(_NOMINATIM_REVERSE_URL).mock(
        return_value=httpx.Response(200, json=_REVERSE_PARIS)
    )
    client = NominatimClient()
    result = await client.reverse_geocode_postal(48.8566, 2.3522)
    await client.close()
    assert result == "75004"


@pytest.mark.asyncio
@respx.mock
async def test_reverse_geocode_postal_missing_postcode() -> None:
    respx.get(_NOMINATIM_REVERSE_URL).mock(
        return_value=httpx.Response(200, json=_REVERSE_NO_POSTCODE)
    )
    client = NominatimClient()
    result = await client.reverse_geocode_postal(0.0, 0.0)
    await client.close()
    assert result is None


# ── _parse_establishment: category code from multi-type array ────────────────


def test_parse_establishment_picks_category_system() -> None:
    """The parser must find TRE-R66 code even when it is not the first type entry."""
    from annuaire_mcp.client import _parse_establishment

    resource = {
        "resourceType": "Organization",
        "type": [
            {
                "coding": [
                    {
                        "system": "https://hl7.fr/ig/fhir/core/CodeSystem/fr-core-cs-v2-3307",
                        "code": "GEOGRAPHICAL-ENTITY",
                    }
                ]
            },
            {
                "coding": [
                    {
                        "system": (
                            "https://mos.esante.gouv.fr/NOS/"
                            "TRE_R66-CategorieEtablissement/FHIR/"
                            "TRE-R66-CategorieEtablissement"
                        ),
                        "code": "500",
                        "display": "Etablissement d'hebergement pour personnes agees dependantes",
                    }
                ]
            },
        ],
    }
    est = _parse_establishment(resource)
    assert est.category_code == "500"
    assert est.category_label is not None


# ── search_establishments (integration via mcp.call_tool) ────────────────────


def _parse_tool_result(result) -> dict:
    return json.loads(result.content[0].text)


@pytest.mark.asyncio
@respx.mock
async def test_search_establishments_success() -> None:
    respx.get(_NOMINATIM_REVERSE_URL).mock(
        return_value=httpx.Response(200, json=_REVERSE_PARIS)
    )
    respx.get(_FHIR_ORG_URL).mock(
        return_value=httpx.Response(200, json=FHIR_BUNDLE_ONE_ORG)
    )

    from annuaire_mcp.main import mcp

    result = await mcp.call_tool(
        "search_establishments",
        {"latitude": 48.8566, "longitude": 2.3522, "radius_km": 5, "category": "EHPAD"},
    )
    data = _parse_tool_result(result)
    assert data["count"] == 1
    assert data["establishments"][0]["name"] == "EHPAD Les Pins"


@pytest.mark.asyncio
@respx.mock
async def test_search_establishments_fallback_to_department() -> None:
    """When the exact postal code yields 0 results, the tool widens to department."""
    respx.get(_NOMINATIM_REVERSE_URL).mock(
        return_value=httpx.Response(200, json=_REVERSE_PARIS)
    )
    fhir_route = respx.get(_FHIR_ORG_URL)
    fhir_route.side_effect = [
        httpx.Response(200, json=FHIR_BUNDLE_EMPTY),
        httpx.Response(200, json=FHIR_BUNDLE_ONE_ORG),
    ]

    from annuaire_mcp.main import mcp

    result = await mcp.call_tool(
        "search_establishments",
        {"latitude": 48.8566, "longitude": 2.3522, "radius_km": 5, "category": "EHPAD"},
    )
    data = _parse_tool_result(result)
    assert data["count"] == 1
    assert fhir_route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_search_establishments_no_fallback_when_large_radius() -> None:
    """With radius > 10 km the first call already uses the department prefix: no fallback."""
    respx.get(_NOMINATIM_REVERSE_URL).mock(
        return_value=httpx.Response(200, json=_REVERSE_PARIS)
    )
    fhir_route = respx.get(_FHIR_ORG_URL)
    fhir_route.mock(return_value=httpx.Response(200, json=FHIR_BUNDLE_ONE_ORG))

    from annuaire_mcp.main import mcp

    result = await mcp.call_tool(
        "search_establishments",
        {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "radius_km": 20,
            "category": "EHPAD",
        },
    )
    data = _parse_tool_result(result)
    assert data["count"] == 1
    assert fhir_route.call_count == 1


@pytest.mark.asyncio
async def test_search_establishments_invalid_category() -> None:
    from annuaire_mcp.main import mcp

    with pytest.raises(Exception, match="Unknown category"):
        await mcp.call_tool(
            "search_establishments",
            {
                "latitude": 48.8566,
                "longitude": 2.3522,
                "radius_km": 5,
                "category": "UNKNOWN",
            },
        )
