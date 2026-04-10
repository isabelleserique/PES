from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Sistema TCC ICOMP"
    app_env: str = "development"
    app_debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:4200"

    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/sistema_tcc_icomp",
        alias="DATABASE_URL",
    )
    direct_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/sistema_tcc_icomp",
        alias="DIRECT_URL",
    )

    jwt_secret: str = "troque-esta-chave-em-producao"
    jwt_algorithm: str = "HS256"
    session_timeout_hours: int = 8

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    smtp_timeout_seconds: int = 20
    smtp_test_recipient: str = ""

    mailtrap_host: str = "sandbox.smtp.mailtrap.io"
    mailtrap_port: int = 2525
    mailtrap_user: str = ""
    mailtrap_pass: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()

