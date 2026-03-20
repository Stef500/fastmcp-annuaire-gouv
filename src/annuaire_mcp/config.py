"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    esante_api_key: str
    fhir_base_url: str = "https://gateway.api.esante.gouv.fr/fhir/v2"
    http_timeout: float = 30.0
    max_results: int = 50


def get_settings() -> Settings:
    """Return the application settings singleton."""
    return Settings()  # type: ignore[call-arg]
