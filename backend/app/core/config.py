from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Core
    DATABASE_URL: str = "postgresql+asyncpg://nexus:nexus@localhost:5432/nexus_credit"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "nexus-hackathon-secret-key-2026-dev-only"
    CORS_ORIGINS: str = "*"

    # AI
    ANTHROPIC_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    # Financial Data
    ALPHA_VANTAGE_API_KEY: str = ""
    DUCKDB_PATH: str = "./data/nexus_demo.duckdb"

    # Databricks
    DATABRICKS_HOST: str = ""
    DATABRICKS_TOKEN: str = ""
    DATABRICKS_CLUSTER_ID: str = ""

    # Demo
    DEMO_MODE: bool = True
    DEMO_PROCESSING_SPEED_MULTIPLIER: int = 10

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
