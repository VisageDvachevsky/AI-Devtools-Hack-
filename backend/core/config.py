from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Devtools Hack"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    MCP_SERVER_URL: str = "http://mcp_server:8001"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    EVOLUTION_API_KEY: str = ""
    EVOLUTION_API_URL: str = "https://api.example.com/v1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
