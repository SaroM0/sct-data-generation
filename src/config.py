"""Configuration for SCT data generation."""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # LLM Provider Configuration
    llm_provider: str = "openai"  # "openai" or "gemini"

    # OpenAI Configuration
    openai_api_key: str = ""

    # Gemini Configuration
    gemini_api_key: str = ""

    # Generation Configuration
    num_scts_to_generate: int
    model: str

    # Domain Distribution (comma-separated list)
    domain_distribution: str

    # Logging
    log_level: str = "INFO"

    @property
    def domains(self) -> List[str]:
        """Parse domain distribution into a list."""
        return [d.strip() for d in self.domain_distribution.split(",") if d.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
