"""
Configuration du système de logging
"""
import logging
import sys
from typing import Dict, Any
from app.config import settings


class ColoredFormatter(logging.Formatter):
    """Formatter avec couleurs pour les logs"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Vert
        'WARNING': '\033[33m',  # Jaune
        'ERROR': '\033[31m',    # Rouge
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging() -> None:
    """Configure le système de logging"""
    
    # Configuration du logger principal
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Supprime les handlers existants
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler pour la console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Formatter avec couleurs
    formatter = ColoredFormatter(settings.log_format)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # Configuration des loggers spécifiques
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger configuré"""
    return logging.getLogger(name)


def log_request_info(request_id: str, endpoint: str, method: str, user_id: str = None) -> None:
    """Log les informations de requête"""
    logger = get_logger("api.request")
    logger.info(
        f"Request [{request_id}] - {method} {endpoint} - User: {user_id or 'Anonymous'}"
    )


def log_conversion_info(request_id: str, filename: str, file_size: int, processing_time: float) -> None:
    """Log les informations de conversion"""
    logger = get_logger("api.conversion")
    logger.info(
        f"Conversion [{request_id}] - File: {filename} ({file_size} bytes) - "
        f"Processing time: {processing_time:.2f}s"
    )


def log_error(request_id: str, error: Exception, context: Dict[str, Any] = None) -> None:
    """Log les erreurs avec contexte"""
    logger = get_logger("api.error")
    context_str = f" - Context: {context}" if context else ""
    logger.error(
        f"Error [{request_id}] - {type(error).__name__}: {str(error)}{context_str}",
        exc_info=True
    )