from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Load from .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Neo4j
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    # Gemma
    GEMMA_MODEL_ID: str
    HF_TOKEN: Optional[str] = None

    # Paths
    FAISS_INDEX_PATH: str
    CSV_PATH: str


settings = Settings()