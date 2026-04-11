"""Configuration and secrets for the RemoteBatch application."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    remote_batch_bucket: str = "remote-batch-bucket"


settings = Settings()
REMOTE_BATCH_BUCKET = settings.remote_batch_bucket
