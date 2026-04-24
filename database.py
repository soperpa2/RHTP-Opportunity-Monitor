from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = ""
    app_env: str = "local"
    app_secret: str = "change-me"
    crawl_timeout_seconds: int = 20
    crawl_user_agent: str = "RHTP Opportunity Monitor/1.0"
    alert_email_to: str = ""
    alert_email_from: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
