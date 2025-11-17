from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import AnyHttpUrl


class Settings(BaseSettings):
  # --- App metadata ---------------------------------------------------------
  APP_NAME: str = "Creative Automation POC"
  APP_VERSION: str = "0.1.0"
  ENV: str = "local"          # local | dev | prod
  DEBUG: bool = False

  # --- DB Configuration ----------------------------------------------------
  DB_URL: str = "postgresql://admin:admin@db:5432/db"

  # --- S3 / Object Storage Configuration ---------------------------------
  S3_ENDPOINT_URL: str = "http://storage:9000"
  S3_ACCESS_KEY: str = "minio"
  S3_SECRET_KEY: str = "minio123"
  S3_BUCKET: str = "assets"
  S3_REGION_NAME: str = "us-east-1"

  # GEMINI_API_KEY: str = ""

  # --- CORS Configuration --------------------------------------------------
  BACKEND_CORS_ORIGINS: List[AnyHttpUrl] | List[str] = ["*"]

  # Pydantic v2 style validator
  @field_validator('BACKEND_CORS_ORIGINS', mode='before')
  def assemble_cors_origins(cls, v: Optional[str | List[str]]):
    """
    Allow either a JSON-style list or a comma-separated string in env.
    Example:
      BACKEND_CORS_ORIGINS='["http://localhost:3000", "https://example.com"]'
    or
      BACKEND_CORS_ORIGINS="http://localhost:3000,https://example.com"
    """
    if isinstance(v, str):
      # Split comma-separated string
      return [i.strip() for i in v.split(",") if i.strip()]
    return v

  class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"
    case_sensitive = True


@lru_cache
def get_settings() -> Settings:
  return Settings()


# Initialize settings globally
settings = get_settings()
