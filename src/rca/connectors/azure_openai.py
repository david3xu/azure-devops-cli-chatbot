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
        # Azure OpenAI settings from environment variables
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        
        # Deployment settings
        self.chat_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        self.chat_model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4")
        
        # Default parameters
        self.default_temperature = float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.5"))
        self.default_max_tokens = int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "2000"))
        
        # Support for gpt-4o-mini model
        self.support_4o_mini = True
        
        # Tracking successful initialization
        self.initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the Azure OpenAI connector.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.initialized:
            return True
            
        try:
            # Validate required settings
            if not self.api_key or not self.endpoint:
                logger.error("Missing required Azure OpenAI settings")
                logger.error(f"API Key: {'Set' if self.api_key else 'Missing'}")
                logger.error(f"Endpoint: {'Set' if self.endpoint else 'Missing'}")
                return False
            
            # Check if model is gpt-4o-mini
            if "gpt-4o-mini" in self.chat_model or "gpt-4o-mini" in self.chat_deployment:
                logger.info("Using gpt-4o-mini model - more efficient and cost-effective")
                self.is_4o_mini = True
            else:
                logger.info(f"Using {self.chat_model} model via {self.chat_deployment} deployment")
                self.is_4o_mini = False
            
            # Test the connection with a simple query
            test_messages = [
                ChatMessage(role="system", content="You are a helpful assistant."),
                ChatMessage(role="user", content="Hello, are you working?")
            ]
            
            response = self.chat_completion(
                messages=test_messages, 
                temperature=0.1,
                max_tokens=20
            )
            
            if response:
                self.initialized = True
                logger.info("Azure OpenAI connector initialized successfully")
                return True
            else:
                logger.error("Failed to get test completion from Azure OpenAI")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing Azure OpenAI connector: {str(e)}")
            return False
    
    def chat_completion(
        self, 
        messages: List[ChatMessage],
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
            # Prepare the chat request
            url = f"{self.endpoint}/openai/deployments/{self.chat_deployment}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            
            params = {
                "api-version": self.api_version
            }
            
            # Convert messages to the expected format
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Prepare the request body
            request_body = {
                "messages": formatted_messages,
                "model": self.chat_model,
                "temperature": temperature if temperature is not None else self.default_temperature,
                "max_tokens": max_tokens if max_tokens is not None else self.default_max_tokens,
                "stream": stream
            }
            
            # Add stop sequences if provided
            if stop_sequences:
                request_body["stop"] = stop_sequences
            
            # Optimize for gpt-4o-mini if using that model
            if self.is_4o_mini:
                # GPT-4o-mini performs better with slightly higher temperature
                if temperature is None or temperature < 0.2:
                    request_body["temperature"] = 0.2
                    
                # Use the seed parameter for more deterministic results
                request_body["seed"] = 123
            
            # Make the request
            start_time = time.time()
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=request_body,
                timeout=60  # Increased timeout for longer responses
            )
            request_time = (time.time() - start_time) * 1000
            
            # Handle streaming responses
            if stream:
                # Return the response object directly for streaming
                return response
            
            # Handle non-streaming responses
            if response.status_code != 200:
                logger.error(f"Chat completion request failed: {response.status_code} - {response.text}")
                return self._get_mock_completion(messages)
            
            result = response.json()
            
            # Log performance metrics
            token_count = result.get("usage", {}).get("total_tokens", 0)
            logger.info(f"Chat completion: {token_count} tokens in {request_time:.2f}ms")
            
            return result
                
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            return self._get_mock_completion(messages)
    
    def _get_mock_completion(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        """
        Get a mock chat completion for development and testing.
        
        Args:
            messages: List of chat messages
            
        Returns:
            Mock chat completion response
        """
        # Extract the last user message to generate a relevant mock response
        last_message = None
        for msg in reversed(messages):
            if msg.role == "user":
                last_message = msg.content
                break
        
        # Generate a mock response based on the user's query
        if last_message:
            if "azure" in last_message.lower() or "devops" in last_message.lower():
                mock_content = "Azure DevOps is a set of development tools and services that help teams plan work, collaborate on code development, and build and deploy applications."
            elif "pipeline" in last_message.lower():
                mock_content = "Azure Pipelines is a cloud service that you can use to automatically build, test, and deploy your code project."
            elif "issue" in last_message.lower() or "problem" in last_message.lower() or "troubleshoot" in last_message.lower():
                mock_content = "When troubleshooting issues, start by checking logs, reviewing recent changes, and examining system metrics to identify the root cause."
            else:
                mock_content = "I'm a mock assistant for development. This is a placeholder response since we're not connected to the actual Azure OpenAI service."
        else:
            mock_content = "I'm a mock assistant for development. This is a placeholder response."
        
        # Create a mock OpenAI API response
        mock_response = {
            "id": "mock-completion-id",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "mock-model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": mock_content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": sum(len(msg.content.split()) for msg in messages),
                "completion_tokens": len(mock_content.split()),
                "total_tokens": sum(len(msg.content.split()) for msg in messages) + len(mock_content.split())
            }
        }
        
        return mock_response
    
    def get_completion_text(self, completion_response: Dict[str, Any]) -> str:
        """
        Extract the completion text from a chat completion response.
        
        Args:
            completion_response: Chat completion response
            
        Returns:
            Completion text
        """
        try:
            return completion_response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            logger.error("Failed to extract completion text from response")
            return "" 