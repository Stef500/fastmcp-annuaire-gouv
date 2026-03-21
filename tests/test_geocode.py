"""Tests for the geocode_address MCP tool."""

import httpx
import pytest
import respx

from annuaire_mcp.tools import _NOMINATIM_URL

NOMINATIM_HIT = [
    {
        "lat": "48.8566",
        "lon": "2.3522",
        "display_name": "Paris, Ile-de-France, France metropolitaine, France",
    }
]

NOMINATIM_EMPTY: list = []


def _parse_result(result) -> dict:
    import json
    text = result.content[0].text
    return json.loads(text)


@pytest.mark.asyncio
@respx.mock
async def test_geocode_address_found() -> None:
    respx.get(_NOMINATIM_URL).mock(
        return_value=httpx.Response(200, json=NOMINATIM_HIT)
    )

    from annuaire_mcp.main import mcp

    result = await mcp.call_tool("geocode_address", {"address": "Paris"})
    parsed = _parse_result(result)
    assert parsed["latitude"] == 48.8566
    assert parsed["longitude"] == 2.3522
    assert "Paris" in parsed["display_name"]


@pytest.mark.asyncio
@respx.mock
async def test_geocode_address_not_found() -> None:
    respx.get(_NOMINATIM_URL).mock(
        return_value=httpx.Response(200, json=NOMINATIM_EMPTY)
    )

    from annuaire_mcp.main import mcp

    result = await mcp.call_tool("geocode_address", {"address": "zzz-inexistant-zzz"})
    parsed = _parse_result(result)
    assert "error" in parsed
