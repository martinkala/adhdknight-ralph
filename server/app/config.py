from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    environment: str = "development"

    # Monitoring (FR-004–FR-012a) — see app/monitoring/
    monitoring_api_key: str = "change-me-in-production"
    monitoring_account_email: str = "monitor@adhdknight.internal"
    monitoring_account_password: str = "change-me-in-production"
    monitoring_check_interval_minutes: int = 15
    monitoring_escalation_threshold: int = 2  # FR-008a: consecutive failures (N) before escalation
    monitoring_api_base_url: str = "http://127.0.0.1:8095"
    monitoring_web_console_base_url: str = "http://127.0.0.1:8000"
    integrity_user_count_growth_threshold: int = 20  # FR-010
    integrity_user_data_growth_threshold: int = 100  # FR-012

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
