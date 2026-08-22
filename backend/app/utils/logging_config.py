"""
Logging configuration for production
"""

import logging
import json
from pythonjsonlogger import jsonlogger
from datetime import datetime
import os


def setup_logging():
    """Setup JSON logging for production"""
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # JSON formatter
    logHandler = logging.FileHandler("logs/app.log")
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        timestamp=True
    )
    logHandler.setFormatter(formatter)
    root_logger.addHandler(logHandler)
    
    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger


# Get logger instance
logger = logging.getLogger(__name__)


class LoggerMixin:
    """Mixin for consistent logging across agents"""
    
    @staticmethod
    def log_info(message: str, **kwargs):
        logger.info(f"{message} | {json.dumps(kwargs)}")
    
    @staticmethod
    def log_error(message: str, error: Exception = None, **kwargs):
        logger.error(f"{message} | Error: {str(error)} | {json.dumps(kwargs)}")
    
    @staticmethod
    def log_warning(message: str, **kwargs):
        logger.warning(f"{message} | {json.dumps(kwargs)}")
