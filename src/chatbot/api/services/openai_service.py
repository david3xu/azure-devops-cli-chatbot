"""
Service for interacting with Azure OpenAI API.
Includes error handling, retry logic, and telemetry.
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

import openai
from openai import AzureOpenAI
from openai._exceptions import APIError, RateLimitError
from openai.types.chat import ChatCompletion

from src.chatbot.config.settings import settings
from src.chatbot.utils.logging import get_logger, log_conversation_metrics

# Configure logger
logger = get_logger(__name__)


class AzureOpenAIService:
    """Service for interacting with Azure OpenAI API with proper error handling and retry logic."""
    
    def __init__(self):
        """Initialize the Azure OpenAI client."""
        self.client = None
        self.initialized = False
        self.max_retries = 3
        self.retry_delay = 1  # starting delay in seconds
        
    def initialize(self) -> bool:
        """
        Initialize the Azure OpenAI client with settings.
        Returns True if successful, False otherwise.
        """
        if self.initialized:
            return True
            
        try:
            # Validate required settings
            if not settings.validate():
                logger.error("Missing required Azure OpenAI settings")
                return False
                
            # Log the settings being used
            logger.info(f"Initializing Azure OpenAI client with endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
            logger.info(f"Using deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
                
            # Use Azure OpenAI client 
            self.client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                timeout=10.0  # Increase timeout for more reliability
            )
            
            self.initialized = True
            logger.info("Azure OpenAI client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}", exc_info=e)
            return False
            
    def _handle_retry(self, func, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute a function with retry logic.
        
        Args:
            func: The function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function or raises an exception after max retries
        """
        if not self.initialized and not self.initialize():
            raise RuntimeError("Azure OpenAI client not initialized")
            
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                if retries > 0:
                    logger.info(f"Retry attempt {retries}/{self.max_retries}")
                    
                return func(*args, **kwargs)
                
            except RateLimitError as e:
                last_error = e
                # Exponential backoff for rate limit errors
                delay = self.retry_delay * (2 ** retries)
                logger.warning(f"Rate limit reached, retrying in {delay}s", exc_info=e)
                time.sleep(delay)
                
            except openai.APITimeoutError as e:
                last_error = e
                delay = self.retry_delay
                logger.warning(f"Request timed out, retrying in {delay}s", exc_info=e)
                time.sleep(delay)
                
            except APIError as e:
                # Only retry on certain status codes
                if hasattr(e, 'status_code') and e.status_code in (408, 429, 500, 502, 503, 504):
                    last_error = e
                    delay = self.retry_delay
                    logger.warning(f"API error {e.status_code}, retrying in {delay}s", exc_info=e)
                    time.sleep(delay)
                else:
                    # Don't retry on other API errors
                    logger.error(f"API error", exc_info=e)
                    raise
                    
            except Exception as e:
                # Don't retry on other exceptions
                logger.error("Unexpected error", exc_info=e)
                raise
                
            retries += 1
            
        # If we've exhausted retries, raise the last error
        logger.error(f"Exhausted {self.max_retries} retries", exc_info=last_error)
        raise last_error
        
    def chat_completion(
        self, 
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get a chat completion from Azure OpenAI API with retry logic and metrics.
        
        Args:
            messages: List of message objects with role and content
            temperature: Temperature for response generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            The API response as a dictionary
        """
        start_time = time.time()
        success = False
        tokens_used = 0
        error_type = None
        
        try:
            def _get_completion():
                # Ensure we're using the correct endpoint
                endpoint_url = settings.AZURE_OPENAI_ENDPOINT.strip()
                if not endpoint_url.startswith('https://'):
                    endpoint_url = f"https://{endpoint_url}"
                logger.debug(f"Using endpoint: {endpoint_url}")
                
                return self.client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            
            response = self._handle_retry(_get_completion)
            
            # Extract token usage
            tokens_used = (
                response.usage.total_tokens 
                if hasattr(response, "usage") and hasattr(response.usage, "total_tokens")
                else 0
            )
            
            success = True
            return response
            
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error in chat completion: {str(e)}", exc_info=e)
            raise
            
        finally:
            # Log metrics regardless of success/failure
            duration_ms = (time.time() - start_time) * 1000
            log_conversation_metrics(
                duration_ms=duration_ms,
                tokens_used=tokens_used,
                success=success,
                error_type=error_type,
            )

# Create a global instance
openai_service = AzureOpenAIService() 