"""Shared pytest fixtures."""

import pytest

from annuaire_mcp.config import Settings


@pytest.fixture(autouse=True)
def clear_geocode_cache() -> None:
    """Clear the reverse geocoding cache before each test for mock isolation."""
    from annuaire_mcp.main import _nominatim_client

    _nominatim_client._reverse_cache.clear()


@pytest.fixture()
def settings() -> Settings:
    """Return a Settings instance with a dummy API key for testing."""
    return Settings(esante_api_key="test-key-00000")


FHIR_BUNDLE_ONE_ORG = {
    "resourceType": "Bundle",
    "total": 1,
    "entry": [
        {
            "resource": {
                "resourceType": "Organization",
                "id": "org-1",
                "active": True,
                "name": "EHPAD Les Pins",
                "identifier": [
                    {
                        "system": "https://finess.esante.gouv.fr",
                        "value": "750123456",
                    }
                ],
                "type": [
                    {
                        "coding": [
                            {
                                "system": (
                                    "https://mos.esante.gouv.fr/NOS/"
                                    "TRE_R66-CategorieEtablissement/FHIR/"
                                    "TRE-R66-CategorieEtablissement"
                                ),
                                "code": "500",
                                "display": "Etablissement d'Hebergement pour Personnes Agees Dependantes",
                            }
                        ]
                    }
                ],
                "telecom": [{"system": "phone", "value": "0101020304", "use": "work"}],
                "address": [
                    {
                        "line": ["10 rue des Pins"],
                        "city": "Paris",
                        "postalCode": "75001",
                        "country": "FR",
                    }
                ],
                "extension": [
                    {
                        "url": "https://hl7.fr/fhir/fr/core/StructureDefinition/fr-core-address-point-geo-fhir-geolocation",
                        "extension": [
                            {"url": "latitude", "valueDecimal": 48.8566},
                            {"url": "longitude", "valueDecimal": 2.3522},
                        ],
                    }
                ],
            }
        }
    ],
}

FHIR_BUNDLE_EMPTY = {
    "resourceType": "Bundle",
    "total": 0,
    "entry": [],
}
