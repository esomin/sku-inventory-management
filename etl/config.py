"""
Configuration management for GPU Price Monitoring ETL System.

This module uses pydantic-settings to load configuration from environment variables
and .env files, providing type-safe access to all system settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    All settings have sensible defaults and can be overridden via environment variables.
    """
    
    # Database Configuration
    db_host: str = Field(default="localhost", description="PostgreSQL host")
    db_port: int = Field(default=5432, description="PostgreSQL port")
    db_name: str = Field(default="gpu_etl", description="Database name")
    db_user: str = Field(default="postgres", description="Database user")
    db_password: str = Field(description="Database password (required)")
    
    # Scheduler Configuration
    price_crawl_hour: int = Field(default=9, ge=0, le=23, description="Hour to run price crawl (0-23)")
    price_crawl_minute: int = Field(default=0, ge=0, le=59, description="Minute to run price crawl (0-59)")
    reddit_crawl_hour: int = Field(default=10, ge=0, le=23, description="Hour to run Reddit collection (0-23)")
    reddit_crawl_minute: int = Field(default=0, ge=0, le=59, description="Minute to run Reddit collection (0-59)")
    
    # Risk Calculation Configuration
    risk_threshold: float = Field(default=100.0, description="Risk index threshold for alerts")
    sentiment_weight_new_release: float = Field(default=3.0, description="Weight for 'New Release' keyword")
    sentiment_weight_price_drop: float = Field(default=2.0, description="Weight for 'Price Drop' keyword")
    sentiment_weight_default: float = Field(default=1.0, description="Default weight for other keywords")
    
    # Retry Configuration
    max_retries: int = Field(default=3, ge=1, description="Maximum retry attempts for operations")
    retry_backoff_seconds: int = Field(default=5, ge=1, description="Initial backoff time for retries")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    def get_sentiment_weight(self, keyword: str) -> float:
        """
        Get sentiment weight for a given keyword.
        
        Args:
            keyword: The keyword to get weight for
            
        Returns:
            Weight value for the keyword
        """
        keyword_lower = keyword.lower()
        if "new release" in keyword_lower or "leak" in keyword_lower:
            return self.sentiment_weight_new_release
        elif "price drop" in keyword_lower:
            return self.sentiment_weight_price_drop
        else:
            return self.sentiment_weight_default


# Global settings instance
settings = Settings()
