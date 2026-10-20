from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "vector-studio-ryan-vo"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./vector_studio.db"
    
    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OIDC / Keycloak
    oidc_enabled: bool = True
    oidc_client_id: str = "vector-studio"
    oidc_client_secret: str = ""
    oidc_issuer_url: str = "http://localhost:8080/realms/vector-studio"
    oidc_redirect_uri: str = "http://localhost:5173/callback"
    oidc_logout_uri: str = "http://localhost:5173"
    
    # LLM
    llm_api_key: Optional[str] = None
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: Optional[str] = None
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()