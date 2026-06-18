"""
HR Assist Pro - Logging Configuration

Professional logging setup for the application.
"""

import logging
import logging.handlers
import os
from datetime import datetime

from config import config


def setup_logging():
    """Configure professional logging for the application."""
    
    # Create logs directory if it doesn't exist
    os.makedirs(config.LOGS_PATH, exist_ok=True)
    
    # Log file path with timestamp
    log_file = os.path.join(
        config.LOGS_PATH,
        f"hr-assist-pro-{datetime.now().strftime('%Y-%m-%d')}.log"
    )
    
    # Create logger
    logger = logging.getLogger("hr_assist_pro")
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler (detailed)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler (simple)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


# Create global logger instance
logger = setup_logging() if config.ENABLE_LOGGING else logging.getLogger("hr_assist_pro")
