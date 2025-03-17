"""
Conversation models for the RCA system.
Provides Pydantic models for managing conversation context in the RAG pipeline.
"""
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class ConversationMessage(BaseModel):
    """A message in a conversation."""
    id: UUID = Field(default_factory=uuid4)
    role: str = Field(..., description="Role of the message sender: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Content of the message")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert the message to a dictionary for API requests."""
        return {"role": self.role, "content": self.content}


class Conversation(BaseModel):
    """
    Manages a conversation with message history and context.
    Handles the conversation context for a Root Cause Analysis session.
    """
    id: UUID = Field(default_factory=uuid4)
    system_prompt: str = Field(..., description="System prompt providing context and instructions")
    messages: List[ConversationMessage] = Field(default_factory=list)
    max_history: int = Field(default=10, description="Maximum number of messages to keep in history")
    metadata: Dict[str, Union[str, int, bool, Dict, List]] = Field(default_factory=dict)
    user_id: Optional[str] = Field(default=None, description="ID of the user associated with this conversation")
    session_id: Optional[str] = Field(default=None, description="ID of the session this conversation belongs to")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_message(self, role: str, content: str) -> ConversationMessage:
        """Add a message to the conversation history."""
        message = ConversationMessage(role=role, content=content)
        self.messages.append(message)
        self._trim_history()
        self.updated_at = datetime.utcnow()
        return message
    
    def add_user_message(self, content: str) -> ConversationMessage:
        """Add a user message to the conversation history."""
        return self.add_message("user", content)
    
    def add_assistant_message(self, content: str) -> ConversationMessage:
        """Add an assistant message to the conversation history."""
        return self.add_message("assistant", content)
    
    def _trim_history(self) -> None:
        """
        Trim the conversation history to maximum length.
        Always keeps the system prompt as the first message.
        """
        if len(self.messages) <= self.max_history:
            return
        
        # Keep system messages and most recent messages
        system_messages = [m for m in self.messages if m.role == "system"]
        non_system_messages = [m for m in self.messages if m.role != "system"]
        
        # Keep most recent messages up to max_history - len(system_messages)
        max_non_system = max(0, self.max_history - len(system_messages))
        recent_messages = non_system_messages[-max_non_system:] if max_non_system > 0 else []
        
        # Combine system messages with recent messages
        self.messages = system_messages + recent_messages
    
    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """Get the messages in a format ready for the API."""
        return [message.to_dict() for message in self.messages]
    
    def initialize(self) -> None:
        """Initialize the conversation with the system prompt."""
        # Only add system prompt if no system messages exist
        if not any(m.role == "system" for m in self.messages):
            self.add_message("system", self.system_prompt)
    
    def clear_messages(self) -> None:
        """Clear all messages except the system prompt."""
        system_messages = [m for m in self.messages if m.role == "system"]
        # If no system messages, add the system prompt
        if not system_messages:
            self.messages = [ConversationMessage(role="system", content=self.system_prompt)]
        else:
            self.messages = system_messages
        self.updated_at = datetime.utcnow() 