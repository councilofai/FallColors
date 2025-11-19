"""Configuration settings for the Chatbot Testbed Platform."""

from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    llm_provider: str = "anthropic"  # 'anthropic' or 'openai'

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Testing Configuration
    default_max_rounds: int = 10
    default_adversarial_intensity: int = 5
    screenshot_interval: int = 2
    browser_headless: bool = False

    # Database
    database_url: str = "sqlite:///./chatbot_testbed.db"

    # Security
    secret_key: str = "change-this-in-production"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
