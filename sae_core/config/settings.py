"""
SAE Core Configuration - Centralized configuration management.

This module provides typed configuration for all SAE Core components.
Secrets are never exposed to the frontend.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = "sqlite:///./sae_core.db"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False  # SQL logging
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load configuration from environment variables."""
        return cls(
            url=os.getenv("DATABASE_URL", "sqlite:///./sae_core.db"),
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true"
        )


@dataclass
class AuthConfig:
    """Authentication configuration."""
    secret_key: str = "change-me-in-production"  # Must be overridden in production
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Load configuration from environment variables."""
        secret = os.getenv("AUTH_SECRET_KEY")
        if not secret:
            raise ValueError("AUTH_SECRET_KEY environment variable is required")
        return cls(
            secret_key=secret,
            algorithm=os.getenv("AUTH_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("AUTH_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        )


@dataclass
class StorageConfig:
    """Storage configuration."""
    checkpoints_dir: str = "./runtime/checkpoints"
    logs_dir: str = "./runtime/logs"
    outputs_dir: str = "./runtime/outputs"
    data_dir: str = "./runtime/data"
    
    @classmethod
    def from_env(cls) -> "StorageConfig":
        """Load configuration from environment variables."""
        return cls(
            checkpoints_dir=os.getenv("CHECKPOINTS_DIR", "./runtime/checkpoints"),
            logs_dir=os.getenv("LOGS_DIR", "./runtime/logs"),
            outputs_dir=os.getenv("OUTPUTS_DIR", "./runtime/outputs"),
            data_dir=os.getenv("DATA_DIR", "./runtime/data")
        )
    
    def ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        for dir_path in [self.checkpoints_dir, self.logs_dir, self.outputs_dir, self.data_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


@dataclass
class APIConfig:
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:3000"])
    rate_limit_per_minute: int = 100
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        """Load configuration from environment variables."""
        return cls(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            debug=os.getenv("API_DEBUG", "false").lower() == "true",
            cors_origins=os.getenv("API_CORS_ORIGINS", "http://localhost:3000").split(","),
            rate_limit_per_minute=int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "100"))
        )


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Load configuration from environment variables."""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file=os.getenv("LOG_FILE")
        )


@dataclass
class FoundationModelConfig:
    """Foundation Model configuration."""
    enabled: bool = False
    device: str = "cpu"
    precision: str = "fp32"
    checkpoint_path: Optional[str] = None
    batch_size: int = 1
    
    @classmethod
    def from_env(cls) -> "FoundationModelConfig":
        """Load configuration from environment variables."""
        return cls(
            enabled=os.getenv("FOUNDATION_MODEL_ENABLED", "false").lower() == "true",
            device=os.getenv("FOUNDATION_MODEL_DEVICE", "cpu"),
            precision=os.getenv("FOUNDATION_MODEL_PRECISION", "fp32"),
            checkpoint_path=os.getenv("FOUNDATION_MODEL_CHECKPOINT"),
            batch_size=int(os.getenv("FOUNDATION_MODEL_BATCH_SIZE", "1"))
        )


@dataclass
class SAEConfig:
    """Complete SAE Core configuration."""
    database: DatabaseConfig
    auth: AuthConfig
    storage: StorageConfig
    api: APIConfig
    logging: LoggingConfig
    foundation_model: FoundationModelConfig
    environment: str = "development"
    
    @classmethod
    def from_env(cls) -> "SAEConfig":
        """Load complete configuration from environment variables."""
        return cls(
            database=DatabaseConfig.from_env(),
            auth=AuthConfig.from_env(),
            storage=StorageConfig.from_env(),
            api=APIConfig.from_env(),
            logging=LoggingConfig.from_env(),
            foundation_model=FoundationModelConfig.from_env(),
            environment=os.getenv("ENVIRONMENT", "development")
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if self.environment == "production":
            if self.auth.secret_key == "change-me-in-production":
                raise ValueError("AUTH_SECRET_KEY must be set in production")
            if self.api.debug:
                raise ValueError("API_DEBUG must be false in production")


# Global configuration instance
_config: Optional[SAEConfig] = None


def get_config() -> SAEConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = SAEConfig.from_env()
    return _config


def reset_config() -> None:
    """Reset configuration (for testing)."""
    global _config
    _config = None
