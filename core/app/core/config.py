from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Sentinel"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./sentinel.db"
    health_poll_interval_seconds: int = Field(default=30, ge=5, le=3600)
    api_key: str = ""
    plugin_dir: str = "/data/plugins"

    vault_key: str

    class Config:
        env_file = ".env"

settings = Settings()
