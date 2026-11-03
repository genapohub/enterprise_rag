"""Application settings from env (.env.example keys)."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./enterprise_rag.db"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "enterprise_rag_chunks"

    embedding_base_url: str = "https://api.siliconflow.cn/v1"
    embedding_api_key: str = ""
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024
    embedding_stub: str = "auto"  # auto|true|false

    llm_base_url: str = "https://api.deepseek.com"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_stub: str = "auto"

    jwt_secret: str = "changeme-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    bootstrap_admin_user: str = "admin"
    bootstrap_admin_password: str = "changeme"
    bootstrap_admin_display: str = "管理员"

    chunk_size: int = 800
    chunk_overlap: int = 120
    upload_dir: str = "./uploads"
    max_upload_mb: int = 20
    app_version: str = "0.1.0"

    def use_embedding_stub(self) -> bool:
        if self.embedding_stub.lower() == "true":
            return True
        if self.embedding_stub.lower() == "false":
            return False
        return not bool(self.embedding_api_key.strip())

    def use_llm_stub(self) -> bool:
        if self.llm_stub.lower() == "true":
            return True
        if self.llm_stub.lower() == "false":
            return False
        return not bool(self.llm_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
