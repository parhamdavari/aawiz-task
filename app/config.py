from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Evaluations API"
    environment: str = "development"
    database_url: str = "sqlite:///./app.db"
    snapauth_base_url: str = "http://localhost:8080"
    snapauth_jwks_url: str | None = None
    snapauth_api_key: str | None = None
    jwt_audience: str | None = None
    jwt_issuer: str | None = None

    model_config = {
        "env_prefix": "",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @property
    def jwks_url(self) -> str:
        if self.snapauth_jwks_url:
            return self.snapauth_jwks_url
        base = self.snapauth_base_url.rstrip("/")
        return f"{base}/v1/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()

