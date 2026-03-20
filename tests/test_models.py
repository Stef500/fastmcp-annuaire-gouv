"""Tests for the Pydantic models."""

from annuaire_mcp.models import Address, Establishment, SearchResult, Telecom


def test_establishment_defaults() -> None:
    est = Establishment()
    assert est.finess_id is None
    assert est.telecoms == []


def test_establishment_full() -> None:
    est = Establishment(
        finess_id="750123456",
        name="EHPAD Les Pins",
        category_code="500",
        active=True,
        address=Address(
            line=["10 rue des Pins"],
            city="Paris",
            postal_code="75001",
            country="FR",
        ),
        telecoms=[Telecom(system="phone", value="0101020304", use="work")],
        latitude=48.8566,
        longitude=2.3522,
    )
    assert est.finess_id == "750123456"
    assert est.address is not None
    assert est.address.city == "Paris"
    assert len(est.telecoms) == 1
    assert est.telecoms[0].value == "0101020304"


def test_search_result() -> None:
    result = SearchResult(total=1, count=1, establishments=[Establishment(name="Test")])
    assert result.count == 1
    assert result.total == 1
    assert result.establishments[0].name == "Test"


def test_establishment_model_dump_exclude_none() -> None:
    est = Establishment(name="Test", active=True)
    data = est.model_dump(exclude_none=True)
    assert "finess_id" not in data
    assert data["name"] == "Test"
