"""
HR Assist Pro - Professional Configuration Module

This module handles all configuration management for the application.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # API Configuration
    GOOGLE_GENAI_API_KEY: str = os.getenv("GOOGLE_GENAI_API_KEY", "")
    
    # Paths
    CHROMA_DB_PATH: str = "chroma_db"
    SAMPLE_PDFS_PATH: str = "sample_pdfs"
    LOGS_PATH: str = "logs"
    
    # Streamlit Configuration
    STREAMLIT_THEME: str = "dark"
    PAGE_TITLE: str = "HR Assist Pro"
    PAGE_ICON: str = "HR"
    LAYOUT: str = "wide"
    
    # RAG Configuration
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    MAX_RETRIEVED_CHUNKS: int = 20
    RERANK_TOP_K: int = 5
    
    # Model Configuration
    MODEL_NAME: str = "gemini-2.0-flash"
    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 2000
    
    # Feature Flags
    ENABLE_HALLUCINATION_CHECK: bool = True
    ENABLE_GUARDRAILS: bool = True
    ENABLE_LOGGING: bool = True
    
    # Security
    SESSION_TIMEOUT: int = 3600  # seconds
    MAX_FILE_SIZE: int = 50  # MB
    ALLOWED_FILE_TYPES: list = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.ALLOWED_FILE_TYPES is None:
            self.ALLOWED_FILE_TYPES = ["pdf"]
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables."""
        return cls(
            GOOGLE_GENAI_API_KEY=os.getenv("GOOGLE_GENAI_API_KEY", ""),
            CHROMA_DB_PATH=os.getenv("CHROMA_DB_PATH", "chroma_db"),
            SAMPLE_PDFS_PATH=os.getenv("SAMPLE_PDFS_PATH", "sample_pdfs"),
            LOGS_PATH=os.getenv("LOGS_PATH", "logs"),
        )


# Global config instance
config = AppConfig.from_env()
