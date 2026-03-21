"""Tests for the FHIR API client."""

import httpx
import pytest
import respx

from annuaire_mcp.client import FhirClient, _parse_establishment
from annuaire_mcp.config import Settings
from tests.conftest import FHIR_BUNDLE_EMPTY, FHIR_BUNDLE_ONE_ORG


@pytest.fixture()
def client(settings: Settings) -> FhirClient:
    return FhirClient(settings)


def test_parse_establishment_full() -> None:
    resource = FHIR_BUNDLE_ONE_ORG["entry"][0]["resource"]
    est = _parse_establishment(resource)

    assert est.finess_id == "750123456"
    assert est.name == "EHPAD Les Pins"
    assert est.category_code == "500"
    assert est.active is True
    assert est.address is not None
    assert est.address.city == "Paris"
    assert est.latitude == 48.8566
    assert est.longitude == 2.3522
    assert len(est.telecoms) == 1


def test_parse_establishment_minimal() -> None:
    est = _parse_establishment({"resourceType": "Organization"})
    assert est.finess_id is None
    assert est.name is None
    assert est.telecoms == []


@pytest.mark.asyncio
async def test_search_organizations(client: FhirClient, settings: Settings) -> None:
    with respx.mock(base_url=settings.fhir_base_url) as mock:
        mock.get("/Organization").mock(
            return_value=httpx.Response(200, json=FHIR_BUNDLE_ONE_ORG)
        )
        result = await client.search_organizations(
            postal_code="75001",
            category_code="500",
        )

    assert result.total == 1
    assert result.count == 1
    assert result.establishments[0].name == "EHPAD Les Pins"


@pytest.mark.asyncio
async def test_search_organizations_empty(
    client: FhirClient, settings: Settings
) -> None:
    with respx.mock(base_url=settings.fhir_base_url) as mock:
        mock.get("/Organization").mock(
            return_value=httpx.Response(200, json=FHIR_BUNDLE_EMPTY)
        )
        result = await client.search_organizations(
            postal_code="45000",
            category_code="182",
        )

    assert result.count == 0
    assert result.establishments == []


@pytest.mark.asyncio
async def test_get_organization_by_finess_found(
    client: FhirClient, settings: Settings
) -> None:
    with respx.mock(base_url=settings.fhir_base_url) as mock:
        mock.get("/Organization").mock(
            return_value=httpx.Response(200, json=FHIR_BUNDLE_ONE_ORG)
        )
        est = await client.get_organization_by_finess("750123456")

    assert est is not None
    assert est.finess_id == "750123456"


@pytest.mark.asyncio
async def test_get_organization_by_finess_not_found(
    client: FhirClient, settings: Settings
) -> None:
    with respx.mock(base_url=settings.fhir_base_url) as mock:
        mock.get("/Organization").mock(
            return_value=httpx.Response(200, json=FHIR_BUNDLE_EMPTY)
        )
        est = await client.get_organization_by_finess("000000000")

    assert est is None


@pytest.mark.asyncio
async def test_search_raises_on_http_error(
    client: FhirClient, settings: Settings
) -> None:
    with respx.mock(base_url=settings.fhir_base_url) as mock:
        mock.get("/Organization").mock(
            return_value=httpx.Response(403, json={"issue": "Forbidden"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            await client.search_organizations(
                postal_code="75001",
                category_code="500",
            )


@pytest.mark.asyncio
async def test_retry_on_429_then_success(
    client: FhirClient, settings: Settings
) -> None:
    """A 429 response triggers a retry; subsequent success is returned."""
    with respx.mock(base_url=settings.fhir_base_url) as mock:
        route = mock.get("/Organization")
        route.side_effect = [
            httpx.Response(429, json={}),
            httpx.Response(200, json=FHIR_BUNDLE_ONE_ORG),
        ]
        result = await client.search_organizations(
            postal_code="75001",
            category_code="500",
        )

    assert result.count == 1
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_retry_on_503_then_success(
    client: FhirClient, settings: Settings
) -> None:
    """A 503 response triggers a retry; subsequent success is returned."""
    with respx.mock(base_url=settings.fhir_base_url) as mock:
        route = mock.get("/Organization")
        route.side_effect = [
            httpx.Response(503, json={}),
            httpx.Response(200, json=FHIR_BUNDLE_ONE_ORG),
        ]
        result = await client.search_organizations(
            postal_code="75001",
            category_code="500",
        )

    assert result.count == 1
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted_raises(client: FhirClient, settings: Settings) -> None:
    """After all retries, the last 429 raises HTTPStatusError."""
    with respx.mock(base_url=settings.fhir_base_url) as mock:
        mock.get("/Organization").mock(return_value=httpx.Response(429, json={}))
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.search_organizations(
                postal_code="75001",
                category_code="500",
            )

    assert exc_info.value.response.status_code == 429


@pytest.mark.asyncio
async def test_retry_on_timeout_then_success(
    client: FhirClient, settings: Settings
) -> None:
    """A timeout triggers a retry; subsequent success is returned."""
    with respx.mock(base_url=settings.fhir_base_url) as mock:
        route = mock.get("/Organization")
        route.side_effect = [
            httpx.TimeoutException("timed out"),
            httpx.Response(200, json=FHIR_BUNDLE_ONE_ORG),
        ]
        result = await client.search_organizations(
            postal_code="75001",
            category_code="500",
        )

    assert result.count == 1
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_get_organization_by_finess_active_only(
    client: FhirClient, settings: Settings
) -> None:
    """active_only=True adds active=true to FHIR query params."""
    with respx.mock(base_url=settings.fhir_base_url) as mock:
        route = mock.get("/Organization").mock(
            return_value=httpx.Response(200, json=FHIR_BUNDLE_ONE_ORG)
        )
        await client.get_organization_by_finess("750123456", active_only=True)

    assert "active=true" in str(route.calls[0].request.url)
