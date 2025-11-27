import os
import secrets
from functools import lru_cache
from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "tapwork"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://tapwork:tapwork@db:5432/tapwork"
    secret_key: str = "change-this-secret"

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        # Si está en producción y la clave es la por defecto, genera una aleatoria
        environment = info.data.get('environment', 'development')
        if v == "change-this-secret":
            if environment == "production":
                raise ValueError("SECRET_KEY debe ser configurada en producción. Genera una con: python -c 'import secrets; print(secrets.token_urlsafe(32))'")
            else:
                print("⚠️  ADVERTENCIA: Usando SECRET_KEY por defecto. Configura una segura en .env para producción")
        return v

    access_token_exp_minutes: int = 60 * 24
    email_verification_token_exp_minutes: int = 60 * 24
    password_reset_token_exp_minutes: int = 60
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_tls: bool = False
    mail_from: EmailStr = EmailStr("noreply@example.com")
    frontend_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"
    enable_biometric: bool = False
    allowed_origins: str = "*"  # Comma-separated list or "*" for all

    def get_origins_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into a list"""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def alembic_database_url(self) -> str:
        # Alembic cannot work with async drivers directly
        if self.database_url.startswith("postgresql+asyncpg"):
            return self.database_url.replace("+asyncpg", "+psycopg")
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    # Allows overrides in tests and scripts
    return Settings(_env_file=os.getenv("ENV_FILE", ".env"))

