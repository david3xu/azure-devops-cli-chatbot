"""
Service for interacting with Azure OpenAI API.
Includes error handling, retry logic, and telemetry.
"""
import json
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

try:
    import openai
    from openai import AzureOpenAI
    from openai._exceptions import APIError, RateLimitError
    from openai.types.chat import ChatCompletion, ChatCompletionMessage
except ImportError:
    # Mock these if not available
    class AzureOpenAI:
        pass
    class APIError(Exception):
        pass
    class RateLimitError(Exception):
        pass
    ChatCompletion = Dict[str, Any]
    ChatCompletionMessage = Dict[str, Any]

from src.rca.config import settings
from src.rca.models.conversation import ConversationMessage
from src.rca.tracking.workflow import WorkflowTracker
from src.rca.utils.logging import get_logger, log_conversation_metrics
from src.rca.connectors.azure_openai import AzureOpenAIConnector

# Configure logger
logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """Providers for LLM services."""
    AZURE_OPENAI = "azure_openai"
    OPENAI = "openai"
    MOCK = "mock"  # For testing


class ChatMessage(BaseModel):
    """A chat message for the LLM API."""
    role: str = Field(..., description="Role of the message (system, user, assistant)")
    content: str = Field(..., description="Content of the message")
    
    @classmethod
    def from_conversation_message(cls, message: ConversationMessage) -> "ChatMessage":
        """Create a ChatMessage from a ConversationMessage."""
        return cls(role=message.role, content=message.content)
    
    @classmethod
    def from_dict(cls, message_dict: Dict[str, str]) -> "ChatMessage":
        """Create a ChatMessage from a dictionary."""
        return cls(role=message_dict["role"], content=message_dict["content"])


class ChatCompletionRequest(BaseModel):
    """Request for chat completion."""
    messages: List[ChatMessage] = Field(..., description="Messages for the conversation")
    temperature: float = Field(0.7, description="Sampling temperature for response generation")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    workflow_tracker: Optional[WorkflowTracker] = Field(None, description="Workflow tracker for tracing execution")


class ChatCompletionResponse(BaseModel):
    """Response from chat completion."""
    content: str = Field(..., description="Generated content from the LLM")
    tokens_used: int = Field(0, description="Total tokens used in this request and response")
    processing_time_ms: float = Field(0, description="Processing time in milliseconds")
    model: str = Field("", description="Model used for generation")
    provider: LLMProvider = Field(LLMProvider.AZURE_OPENAI, description="Provider used for generation")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Raw response from the provider")
    error: Optional[str] = Field(None, description="Error message if an error occurred")


class LLMService:
    """Service for interacting with Language Model APIs with proper error handling and retry logic."""
    
    def __init__(self, provider: LLMProvider = LLMProvider.AZURE_OPENAI):
        """Initialize the LLM service client."""
        self.provider = provider
        self.initialized = False
        
        # Azure OpenAI connector (only initialized if using Azure)
        self.azure_connector = None if provider != LLMProvider.AZURE_OPENAI else AzureOpenAIConnector()
        
        # OpenAI client (only used if provider is OPENAI)
        self.openai_client = None
            
    def initialize(self) -> bool:
        """
        Initialize the LLM client with settings.
        Returns True if successful, False otherwise.
        """
        if self.initialized:
            return True
            
        try:
            if self.provider == LLMProvider.AZURE_OPENAI:
                # Initialize the Azure connector
                if self.azure_connector is None:
                    self.azure_connector = AzureOpenAIConnector()
                
                result = self.azure_connector.initialize()
                
                if result:
                    self.initialized = True
                    return True
                else:
                    logger.error("Failed to initialize Azure OpenAI connector")
                    return False
                
            elif self.provider == LLMProvider.OPENAI:
                # Standard OpenAI initialization would go here
                logger.error("Standard OpenAI not currently supported")
                return False
            
            elif self.provider == LLMProvider.MOCK:
                # No initialization needed for mock
                self.initialized = True
                return True
                
            else:
                logger.error(f"Unsupported provider: {self.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing LLM service: {str(e)}")
            return False
            
    def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Generate a chat completion response using the provided messages.
        
        Args:
            request: The request containing messages, settings, and optional workflow tracker
            
        Returns:
            ChatCompletionResponse with the generated content and metadata
        """
        # Start timing
        start_time = time.time()
        
        # Use workflow tracker if provided
        workflow_tracker = request.workflow_tracker
        if workflow_tracker:
            workflow_tracker.start_step("llm_completion")
            
        # Check if initialized
        if not self.initialized and not self.initialize():
            error_msg = f"Failed to initialize LLM service for provider {self.provider}"
            logger.error(error_msg)
            
            if workflow_tracker:
                workflow_tracker.end_step("llm_completion", success=False, error=error_msg)
                
            return ChatCompletionResponse(
                content="Error: LLM service not initialized",
                error=error_msg,
                provider=self.provider
            )
            
        try:
            # Prepare return value
            response = ChatCompletionResponse(
                content="",
                provider=self.provider,
                processing_time_ms=0
            )
            
            # Convert messages to format for API
            messages_dict = [
                {"role": msg.role, "content": msg.content}
                for msg in request.messages
            ]
            
            # Log the request
            logger.debug(f"Chat completion request with {len(messages_dict)} messages")
            
            # Handle based on provider
            if self.provider == LLMProvider.AZURE_OPENAI:
                # Use the Azure connector
                completion = self.azure_connector.chat_completion(
                    messages=messages_dict,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )
                
                if completion is None:
                    error_msg = "Failed to get chat completion from Azure OpenAI"
                    logger.error(error_msg)
                    
                    if workflow_tracker:
                        workflow_tracker.end_step("llm_completion", success=False, error=error_msg)
                        
                    return ChatCompletionResponse(
                        content="Error: Failed to get completion",
                        error=error_msg,
                        provider=self.provider,
                        processing_time_ms=(time.time() - start_time) * 1000
                    )
                
                # Parse the response
                if hasattr(completion, 'choices') and len(completion.choices) > 0:
                    response.content = completion.choices[0].message.content
                else:
                    response.content = "No content returned"
                
                # Fill in metadata
                if hasattr(completion, 'model'):
                    response.model = completion.model
                
                if hasattr(completion, 'usage') and hasattr(completion.usage, 'total_tokens'):
                    response.tokens_used = completion.usage.total_tokens
                    
                # Store raw response for debugging
                response.raw_response = completion
                    
            elif self.provider == LLMProvider.MOCK:
                # Mock implementation for testing
                response.content = f"Mock response to: {messages_dict[-1]['content']}"
                response.model = "mock-model"
                response.tokens_used = len(response.content.split())
                
            else:
                error_msg = f"Unsupported provider: {self.provider}"
                logger.error(error_msg)
                
                if workflow_tracker:
                    workflow_tracker.end_step("llm_completion", success=False, error=error_msg)
                    
                return ChatCompletionResponse(
                    content="Error: Unsupported provider",
                    error=error_msg,
                    provider=self.provider,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Calculate processing time
            elapsed_ms = (time.time() - start_time) * 1000
            response.processing_time_ms = elapsed_ms
            
            # Log metrics
            log_conversation_metrics(
                provider=str(self.provider),
                model=response.model, 
                tokens=response.tokens_used,
                duration_ms=elapsed_ms
            )
            
            logger.debug(f"Chat completion completed in {elapsed_ms:.2f}ms with {response.tokens_used} tokens")
            
            # Finish workflow step if tracking
            if workflow_tracker:
                workflow_tracker.end_step("llm_completion", success=True)
                
            return response
            
        except Exception as e:
            error_msg = f"Error in chat completion: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # End workflow step with error
            if workflow_tracker:
                workflow_tracker.end_step("llm_completion", success=False, error=error_msg)
                
            # Return error response
            return ChatCompletionResponse(
                content=f"Error: {str(e)}",
                error=error_msg,
                provider=self.provider,
                processing_time_ms=(time.time() - start_time) * 1000
            )


# Create a global instance
llm_service = LLMService() 