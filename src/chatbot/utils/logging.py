"""
Logging configuration for the chatbot application.
Uses structlog for structured logging with different formatters based on environment.
"""
import logging
import sys
import time
from typing import Any, Dict, Optional

import structlog

from src.chatbot.config.settings import settings


def configure_logging() -> None:
    """Configure logging for the application."""
    # Parse log level from settings
    log_level_str = settings.LOG_LEVEL.strip().upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Set up stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level
    )

    # Define processors for structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Use different processors based on environment
    if settings.is_production:
        # In production, output JSON for easier log aggregation
        processors.append(structlog.processors.JSONRenderer())
    else:
        # In development, use console output for better readability
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
            )
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger with the given name."""
    return structlog.stdlib.get_logger(name)


# Metrics collection functions
def log_conversation_metrics(
    duration_ms: float,
    tokens_used: int,
    success: bool,
    error_type: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log metrics about a chatbot conversation.
    
    Args:
        duration_ms: Time taken for the response in milliseconds
        tokens_used: Number of tokens used in the conversation
        success: Whether the conversation was successful
        error_type: Type of error if not successful
        extra: Additional metrics to log
    """
    if not settings.ENABLE_METRICS:
        return
    
    logger = get_logger("chatbot.metrics")
    
    metrics = {
        "duration_ms": duration_ms,
        "tokens_used": tokens_used,
        "success": success,
    }
    
    if error_type:
        metrics["error_type"] = error_type
        
    if extra:
        metrics.update(extra)
        
    logger.info("conversation_metrics", **metrics)


# Usage example:
# start_time = time.time()
# ... conversation logic ...
# duration_ms = (time.time() - start_time) * 1000
# log_conversation_metrics(duration_ms, 150, True)


# Initialize logging when module is imported
configure_logging() 