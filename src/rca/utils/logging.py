"""
Logging utilities for the RCA system.
"""
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = "INFO"

# Ensure log directory exists
os.makedirs("logs", exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger configured with the standard format.
    
    Args:
        name: The name of the logger (typically __name__ of the calling module)
        
    Returns:
        A configured logger instance
    """
    # Get log level from environment or use default
    log_level_name = os.environ.get("RCA_LOG_LEVEL", DEFAULT_LOG_LEVEL)
    log_level = getattr(logging, log_level_name.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers = []
    
    # Add console handler if not already present
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)
    
    # Add file handler if not already present
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        log_file = f"logs/rca.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)
    
    return logger


def log_execution_metrics(
    duration_ms: float,
    intent: str,
    confidence: float,
    success: bool,
    execution_mode: str,
    error_type: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log metrics for command execution.
    
    Args:
        duration_ms: Execution time in milliseconds
        intent: The detected intent
        confidence: Confidence score for intent detection
        success: Whether the execution was successful
        execution_mode: The execution mode (LEARN, EXECUTE, AUTO)
        error_type: Type of error if not successful
        parameters: Parameters used in execution
    """
    logger = get_logger("execution_metrics")
    
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "duration_ms": duration_ms,
        "intent": intent,
        "confidence": confidence,
        "success": success,
        "execution_mode": execution_mode,
    }
    
    if error_type:
        metrics["error_type"] = error_type
        
    if parameters:
        metrics["parameters"] = parameters
    
    logger.info("Execution metrics", extra={"metrics": metrics})
    
    # Also log to a JSON file for analytics
    try:
        metrics_file = "logs/execution_metrics.jsonl"
        with open(metrics_file, "a") as f:
            f.write(json.dumps(metrics) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write metrics to file: {e}")


def log_conversation_metrics(
    duration_ms: float,
    tokens_used: int,
    success: bool,
    error_type: Optional[str] = None,
) -> None:
    """
    Log metrics for conversation interactions.
    
    Args:
        duration_ms: Processing time in milliseconds
        tokens_used: Number of tokens used in the interaction
        success: Whether the interaction was successful
        error_type: Type of error if not successful
    """
    logger = get_logger("conversation_metrics")
    
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "duration_ms": duration_ms,
        "tokens_used": tokens_used,
        "success": success,
    }
    
    if error_type:
        metrics["error_type"] = error_type
    
    logger.info("Conversation metrics", extra={"metrics": metrics})
    
    # Also log to a JSON file for analytics
    try:
        metrics_file = "logs/conversation_metrics.jsonl"
        with open(metrics_file, "a") as f:
            f.write(json.dumps(metrics) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write metrics to file: {e}") 