"""Pydantic models for FHIR API responses and domain objects."""

from pydantic import BaseModel, Field


class Address(BaseModel):
    """Postal address of a health establishment."""

    line: list[str] = Field(default_factory=list)
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None


class Telecom(BaseModel):
    """Contact information (phone, fax, email, url)."""

    system: str | None = None
    value: str | None = None
    use: str | None = None


class Establishment(BaseModel):
    """Simplified representation of a health establishment."""

    finess_id: str | None = None
    name: str | None = None
    category_code: str | None = None
    category_label: str | None = None
    active: bool | None = None
    address: Address | None = None
    telecoms: list[Telecom] = Field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None


class SearchResult(BaseModel):
    """Result of a geographic search for establishments."""

    total: int | None = None
    count: int
    establishments: list[Establishment]
