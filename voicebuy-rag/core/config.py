from pydantic_settings import BaseSettings
import os
from typing import Optional

class Settings(BaseSettings):
    # Neo4j
    NEO4J_URI:      str = "bolt://127.0.0.1:7687"
    NEO4J_USER:     str = "neo4j"
    NEO4J_PASSWORD: str = "mothie@1409"

    # Gemma
    GEMMA_MODEL_ID: str = "google/gemma-3-1b-it"
    HF_TOKEN:       Optional[str] = None

    # Paths
    FAISS_INDEX_PATH: str = "storage/faiss_index"
    CSV_PATH:         str = "data/products.csv"

    class Config:
        env_file = ".env"

settings = Settings()
