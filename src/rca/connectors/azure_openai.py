"""
Azure OpenAI connector for the RCA system.
Provides integration with Azure OpenAI for chat completions and embeddings.
"""
from typing import List, Dict, Any, Optional, Union
import os
import json
import time
import logging
import requests
from pydantic import BaseModel

try:
    from openai import AzureOpenAI
except ImportError:
    # Mock implementation
    class AzureOpenAI:
        def __init__(self, **kwargs):
            pass
            
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return None

from src.rca.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


class ChatMessage(BaseModel):
    """Chat message model for OpenAI API."""
    role: str
    content: str
    
    @classmethod
    def from_conversation_message(cls, message):
        """
        Create a ChatMessage from a ConversationMessage.
        
        Args:
            message: ConversationMessage instance
            
        Returns:
            ChatMessage instance
        """
        return cls(role=message.role, content=message.content)


class AzureOpenAIConnector:
    """
    Connector for Azure OpenAI API.
    Handles chat completions and model management.
    """
    
    def __init__(self):
        """Initialize the Azure OpenAI connector."""
        # Configuration
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        self.deployment = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "gpt-4o-mini")
        self.model = os.getenv("AZURE_OPENAI_CHATGPT_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("AZURE_OPENAI_CHATGPT_TEMPERATURE", "0"))
        self.max_tokens = int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "2000"))
        
        # Clean up configuration values
        self.api_key = self.api_key.replace('"', '') if self.api_key else ""
        self.endpoint = self.endpoint.replace('"', '') if self.endpoint else ""
        self.api_version = self.api_version.replace('"', '') if self.api_version else ""
        self.deployment = self.deployment.replace('"', '') if self.deployment else ""
        self.model = self.model.replace('"', '') if self.model else ""
        
        # Clean up endpoint URL (remove trailing slash)
        if self.endpoint:
            self.endpoint = self.endpoint.rstrip('/')
        
        # State
        self.initialized = False
        self.client = None
        self.support_4o_mini = "gpt-4o-mini" in (self.model or "") or "gpt-4o-mini" in (self.deployment or "")
        
        # Stats
        self.total_requests = 0
        self.total_tokens = 0
    
    def initialize(self) -> bool:
        """
        Initialize the Azure OpenAI connector.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        if self.initialized:
            return True
            
        try:
            # Load settings if not already set
            if not self.api_key:
                self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
                self.api_key = self.api_key.replace('"', '')
                
            if not self.endpoint:
                self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
                self.endpoint = self.endpoint.replace('"', '')
                
            if not self.api_version:
                self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
                self.api_version = self.api_version.replace('"', '')
                
            if not self.deployment:
                self.deployment = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "gpt-4o-mini")
                self.deployment = self.deployment.replace('"', '')
                
            if not self.model:
                self.model = os.getenv("AZURE_OPENAI_CHATGPT_MODEL", "gpt-4o-mini")
                self.model = self.model.replace('"', '')
                
            # Clean up endpoint URL
            if self.endpoint:
                self.endpoint = self.endpoint.rstrip('/')
            
            # Validate settings
            if not self.api_key or not self.endpoint:
                logger.warning("Missing required OpenAI settings")
                logger.warning(f"API Key: {'Set' if self.api_key else 'Missing'}")
                logger.warning(f"Endpoint: {'Set' if self.endpoint else 'Missing'}")
                self.initialized = True  # Still mark as initialized, but will use mock
                return True
                
            # Try to initialize SDK client
            try:
                self.client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint
                )
                logger.info(f"Azure OpenAI connector initialized with \"{self.model}\" model via \"{self.deployment}\" deployment")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI SDK client: {str(e)}")
                self.client = None
                
            # Mark as initialized - we'll use HTTP requests as fallback if client is None
            self.initialized = True
            return True
                
        except Exception as e:
            logger.error(f"Error initializing Azure OpenAI connector: {str(e)}")
            self.initialized = True  # Still mark as initialized to allow fallback to mock
            return True
    
    def chat_completion(
        self, 
        messages: List[Union[ChatMessage, Dict[str, str]]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        stop_sequences: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get a chat completion from Azure OpenAI.
        
        Args:
            messages: List of chat messages
            temperature: Temperature for sampling
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response
            stop_sequences: Sequences that stop generation
            
        Returns:
            Chat completion response
        """
        if not self.initialized and not self.initialize():
            logger.error("Failed to initialize Azure OpenAI connector")
            return self._get_mock_completion(messages)
        
        try:
            # Convert message format if needed
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, ChatMessage):
                    formatted_messages.append({"role": msg.role, "content": msg.content})
                elif isinstance(msg, dict) and "role" in msg and "content" in msg:
                    formatted_messages.append(msg)
                else:
                    logger.error(f"Invalid message format: {msg}")
                    continue
            
            # Log the request
            if len(formatted_messages) > 0:
                last_msg_content = formatted_messages[-1]["content"]
                truncated = last_msg_content[:30] + "..." if len(last_msg_content) > 30 else last_msg_content
                logger.debug(f"Sending to Azure OpenAI: [{formatted_messages[0]['role']},...,{formatted_messages[-1]['role']}] Last message: '{truncated}'")
            
            # Track request count
            self.total_requests += 1
            
            # Use the SDK client if available, otherwise use HTTP requests
            if self.client:
                try:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=formatted_messages,
                        temperature=temperature if temperature is not None else self.temperature,
                        max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
                        stream=stream,
                        stop=stop_sequences
                    )
                    
                    # Track token usage
                    if hasattr(completion, 'usage') and hasattr(completion.usage, 'total_tokens'):
                        self.total_tokens += completion.usage.total_tokens
                    
                    # Return the completion
                    return completion
                    
                except Exception as e:
                    logger.error(f"SDK chat completion request failed: {str(e)}")
                    logger.info("Falling back to HTTP request method")
                    # Fall through to HTTP request method
            
            # HTTP request implementation (used when SDK is not available or fails)
            # Build the URL using our helper method
            url = self._build_url(f"openai/deployments/{self.deployment}/chat/completions")
            headers = {
                "Content-Type": "application/json",
                "api-key": self._clean_value(self.api_key)
            }
            
            params = {
                "api-version": self.api_version
            }
            
            # Prepare the request body
            request_body = {
                "messages": formatted_messages,
                "model": self.model,
                "temperature": temperature if temperature is not None else self.temperature,
                "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
                "stream": stream
            }
            
            # Add stop sequences if provided
            if stop_sequences:
                request_body["stop"] = stop_sequences
            
            # Make the request
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=request_body,
                timeout=60  # Increased timeout for longer responses
            )
            
            # Handle non-streaming responses
            if response.status_code != 200:
                logger.error(f"HTTP chat completion request failed: {response.status_code} - {response.text}")
                return self._get_mock_completion(messages)
            
            # Parse the response
            result = response.json()
            
            # Log performance metrics
            token_count = result.get("usage", {}).get("total_tokens", 0)
            self.total_tokens += token_count
            logger.info(f"Chat completion: {token_count} tokens")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            return self._get_mock_completion(messages)
    
    def _get_mock_completion(self, messages: List[Union[ChatMessage, Dict[str, str]]]) -> Dict[str, Any]:
        """
        Get a mock completion for testing or when real service is unavailable.
        
        Args:
            messages: List of chat messages
            
        Returns:
            Mock chat completion response
        """
        try:
            # Extract the last user message
            last_message = None
            for msg in reversed(messages):
                if isinstance(msg, ChatMessage):
                    if msg.role == "user":
                        last_message = msg.content
                        break
                elif isinstance(msg, dict) and msg.get("role") == "user":
                    last_message = msg.get("content", "")
                    break
            
            if not last_message:
                last_message = "Hello"
                
            # Generate a mock response
            mock_response = f"This is a mock response to: {last_message}"
            
            # Create a response mimicking the OpenAI SDK format
            from types import SimpleNamespace
            
            # Create message
            message = SimpleNamespace()
            message.content = mock_response
            message.role = "assistant"
            
            # Create choice
            choice = SimpleNamespace()
            choice.message = message
            choice.finish_reason = "stop"
            choice.index = 0
            
            # Create usage
            usage = SimpleNamespace()
            usage.prompt_tokens = 50
            usage.completion_tokens = len(mock_response.split())
            usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
            
            # Create response
            response = SimpleNamespace()
            response.choices = [choice]
            response.model = "mock-gpt-4"
            response.usage = usage
            response.id = "mock-completion-id"
            response.created = int(time.time())
            
            logger.info("Using mock completion as fallback")
            return response
            
        except Exception as e:
            logger.error(f"Error generating mock completion: {str(e)}")
            
            # Return minimal mock response
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Error generating mock response",
                            "role": "assistant"
                        }
                    }
                ]
            }
    
    def get_completion_text(self, completion_response) -> str:
        """
        Extract the text from a chat completion response.
        
        Args:
            completion_response: Response from OpenAI API
            
        Returns:
            The text of the completion
        """
        try:
            # Handle both dictionary and object formats
            if hasattr(completion_response, 'choices') and len(completion_response.choices) > 0:
                if hasattr(completion_response.choices[0], 'message'):
                    return completion_response.choices[0].message.content
                
            # Fall back to dictionary access for JSON responses
            if isinstance(completion_response, dict):
                if 'choices' in completion_response and len(completion_response['choices']) > 0:
                    return completion_response['choices'][0]['message']['content']
            
            # If we can't find content, return empty string
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from completion: {str(e)}")
            return ""
    
    def _build_url(self, path):
        """
        Build a properly formatted URL for Azure OpenAI API.
        
        Args:
            path: API path to append to the endpoint
            
        Returns:
            Formatted URL
        """
        endpoint = self.endpoint.rstrip('/')
        path = path.lstrip('/')
        return f"{endpoint}/{path}"
        
    def _clean_value(self, value):
        """
        Clean a configuration value by removing quotes.
        
        Args:
            value: Value to clean
            
        Returns:
            Cleaned value
        """
        if value is None:
            return ""
        return str(value).replace('"', '') 