from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg2://wheretoto:wheretoto@localhost:5432/wheretoto"
    cors_origins: str = "http://localhost:3000"

    # Google Places (New) API — only needed to run
    # app/ingestion/enrichment/google_places_photos.py. Unset by default;
    # the script refuses to run without it rather than silently no-op'ing.
    google_places_api_key: str | None = None
    # Where downloaded venue photos are written to disk, and the base URL
    # they're served back from (mounted as static files in app/main.py).
    # In production, point media_public_base_url at wherever this directory
    # is actually served (e.g. a CDN in front of it) — it does not have to
    # be this same API process.
    media_dir: str = "media"
    media_public_base_url: str = "http://localhost:8000/media"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
