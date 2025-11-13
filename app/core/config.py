from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import secrets


class Settings(BaseSettings):
    # IBM Watsonx Settings
    watsonx_api_key: Optional[str] = None
    watsonx_project_id: Optional[str] = None
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"
    watsonx_model_id: str = "ibm/granite-13b-instruct-v1"

    # Pinecone Settings
    pinecone_api_key: Optional[str] = None
    pinecone_env: Optional[str] = None
    index_name: str = "smartcity-policies"

    # Application Settings
    debug: bool = True
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    frontend_port: int = 8501

    # Database
    database_url: str = (
        "mysql+pymysql://smartcity_user:smartcity_pass@localhost:3306/smartcity_db"
    )

    # Security / Auth
    jwt_secret_key: Optional[str] = None  # maps from JWT_SECRET_KEY
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # CORS (comma-separated string in .env)
    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    # Pydantic Settings
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def effective_jwt_secret(self) -> str:
        """Ensure a secret key is always available (warn if using ephemeral)."""
        return self.jwt_secret_key or secrets.token_urlsafe(32)

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list parsed from comma-separated string."""
        if isinstance(self.cors_origins, str):
            return [s.strip() for s in self.cors_origins.split(",") if s.strip()]
        # Fallback in case env provided JSON array (rare)
        try:
            return list(self.cors_origins)  # type: ignore[arg-type]
        except Exception:
            return ["*"]


settings = Settings()
