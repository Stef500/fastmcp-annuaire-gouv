"""Application configuration loaded from environment variables."""

import functools
import logging

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configuration for the MCP server.

    All settings can be set via environment variables or a .env file.
    The ESANTE_API_KEY is mandatory; all other settings have defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    esante_api_key: SecretStr
    fhir_base_url: str = "https://gateway.api.esante.gouv.fr/fhir/v2"
    http_timeout: float = Field(default=30.0, gt=0)
    max_results: int = Field(default=50, ge=1, le=500)

    @field_validator("fhir_base_url")
    @classmethod
    def fhir_url_must_be_https(cls, v: str) -> str:
        """Warn when fhir_base_url is not HTTPS to prevent API key leakage."""
        if not v.startswith("https://"):
            logger.warning(
                "fhir_base_url uses a non-HTTPS scheme; "
                "the API key will be transmitted in plain text"
            )
        return v


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the application settings singleton."""
    return Settings()  # type: ignore[call-arg]
