from typing import Literal

from pydantic import Field, IPvAnyAddress, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        hide_input_in_errors=True,
    )

    database_url: PostgresDsn
    app_env: Environment = "development"
    app_version: str = Field("0.8.0", min_length=1, max_length=64, pattern=r"^\S+$")
    host: IPvAnyAddress = Field(default="127.0.0.1", validate_default=True)
    port: int = Field(8080, ge=1, le=65535)
    log_level: Literal["debug", "info", "warning", "error"] = "info"


def get_settings() -> Settings:
    return Settings.model_validate({})
