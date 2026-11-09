"""
StockVision AI - Application Configuration

Centralized settings using pydantic-settings for environment variable support.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Application
    APP_NAME: str = "StockVision AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./stockvision.db"

    # File storage
    UPLOAD_DIR: str = "uploads"
    MODELS_DIR: str = "models"

    # CORS - allowed origins for the React frontend
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Computer Vision
    YOLO_MODEL_PATH: str = "models/best.pt"
    CV_CONFIDENCE_THRESHOLD: float = 0.5

    # AI Assistant
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Alerts
    LOW_STOCK_CHECK_ENABLED: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton settings instance
settings = Settings()

# Ensure required directories exist
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_PATH = BASE_DIR / settings.UPLOAD_DIR
MODELS_PATH = BASE_DIR / settings.MODELS_DIR

UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
MODELS_PATH.mkdir(parents=True, exist_ok=True)
