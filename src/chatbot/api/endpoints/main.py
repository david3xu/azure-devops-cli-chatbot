"""
Main FastAPI application entry point.
Provides API endpoints for chatbot interaction and health checks.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

from src.chatbot.api.services.execution_service import ExecutionMode
from src.chatbot.config.settings import settings
from src.chatbot.models.conversation import (
    Conversation, 
    DEFAULT_SYSTEM_PROMPT, 
    DEVOPS_CLI_EXPERT_PROMPT,
    EXECUTION_EXPERT_PROMPT
)
from src.chatbot.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Azure DevOps CLI Learning Project Chatbot API",
)


# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    conversation_id: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    mode: Optional[str] = "learn"  # learn, execute, auto
    system_prompt: Optional[str] = None  # Custom system prompt


class ChatResponse(BaseModel):
    """Chat response model."""
    message: str
    conversation_id: str
    execution_info: Optional[Dict] = Field(default=None, description="Information about command execution, if applicable")


# Simple conversation store (in-memory for now, would be replaced by persistent storage)
conversations: Dict[str, Conversation] = {}


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint for interacting with the chatbot.
    
    Creates a new conversation if conversation_id is not provided.
    Supports command execution based on the specified mode.
    """
    conversation_id = request.conversation_id
    execution_mode = ExecutionMode.LEARN  # Default mode
    
    # Parse execution mode
    try:
        if request.mode:
            execution_mode = ExecutionMode(request.mode.lower())
    except ValueError:
        logger.warning(f"Invalid execution mode: {request.mode}, using default")
    
    # Determine system prompt based on mode
    system_prompt = request.system_prompt
    if not system_prompt:
        if execution_mode == ExecutionMode.EXECUTE:
            system_prompt = EXECUTION_EXPERT_PROMPT
        else:
            system_prompt = DEFAULT_SYSTEM_PROMPT
    
    # Create a new conversation if needed
    if not conversation_id or conversation_id not in conversations:
        # Generate a random ID (in production, use UUID)
        import random
        import string
        conversation_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        conversations[conversation_id] = Conversation(system_prompt=system_prompt)
        conversations[conversation_id].set_execution_mode(execution_mode)
        logger.info("Created new conversation", extra={"conversation_id": conversation_id, "mode": execution_mode})
    else:
        # Update execution mode for existing conversation
        conversations[conversation_id].set_execution_mode(execution_mode)
    
    # Get the conversation
    conversation = conversations[conversation_id]
    
    # Add the user message
    conversation.add_user_message(request.message)
    
    # Get a response
    try:
        response = await conversation.get_response(
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        # Check if this was a command execution (look for command in the last assistant message)
        execution_info = None
        if "command was executed" in response or "command would be executed" in response:
            # Extract execution info
            execution_info = {
                "was_executed": "command was executed" in response,
                "mode": execution_mode
            }
        
        return ChatResponse(
            message=response, 
            conversation_id=conversation_id,
            execution_info=execution_info
        )
    except Exception as e:
        logger.error("Error generating response", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to generate response")


@app.on_event("startup")
async def startup_event() -> None:
    """Run startup tasks."""
    logger.info(
        "Starting API",
        extra={
            "host": settings.API_HOST,
            "port": settings.API_PORT,
            "environment": settings.is_production,
        }
    ) 