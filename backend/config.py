from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://forge:forge@localhost:5432/forge"
    secret_key: str = "change-me-in-production"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    gcs_bucket: str = "the-forge-files"
    current_template_version: str = "v1"

    anthropic_api_key: str = ""

    monthly_cost_cap_usd: float = 5.00
    burst_limit_runs: int = 3
    burst_limit_window_minutes: int = 10

    frontend_url: str = "http://localhost:5173"


settings = Settings()
