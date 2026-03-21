"""Tests for the configuration module."""

import pytest
from pydantic import ValidationError

from annuaire_mcp.config import Settings


def test_settings_defaults() -> None:
    s = Settings(esante_api_key="abc123")
    assert s.fhir_base_url == "https://gateway.api.esante.gouv.fr/fhir/v2"
    assert s.http_timeout == 30.0
    assert s.max_results == 50


def test_settings_custom_values() -> None:
    # http:// is accepted with a warning (non-HTTPS is allowed for local dev)
    s = Settings(
        esante_api_key="key",
        fhir_base_url="http://localhost:8080/fhir",
        http_timeout=10.0,
        max_results=10,
    )
    assert s.fhir_base_url == "http://localhost:8080/fhir"
    assert s.max_results == 10


def test_settings_api_key_is_secret() -> None:
    s = Settings(esante_api_key="super-secret-key")
    # SecretStr prevents accidental exposure in repr/str
    assert "super-secret-key" not in repr(s)
    assert s.esante_api_key.get_secret_value() == "super-secret-key"


def test_settings_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ESANTE_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]
