"""
Configuration de l'application
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # Mode développement
    dev_mode: bool = os.getenv("DEV_MODE", "false").lower() == "true"
    disable_auth: bool = os.getenv("DISABLE_AUTH", "false").lower() == "true"
    
    # JWT Configuration
    jwks_url: str = os.getenv("JWKS_URL", "https://example.com/.well-known/jwks.json")
    jwt_algorithm: str = "RS256"
    jwt_audience: Optional[str] = os.getenv("JWT_AUDIENCE")
    jwt_issuer: Optional[str] = os.getenv("JWT_ISSUER")
    
    # API Configuration
    api_title: str = "MSG to PDF Converter API"
    api_description: str = "API pour convertir les fichiers .msg Outlook en PDF"
    api_version: str = "1.0.0"
    
    # File Configuration
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list = [".msg"]
    temp_dir: str = os.getenv("TEMP_DIR", "/tmp")
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"


settings = Settings()