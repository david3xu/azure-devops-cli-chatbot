"""
Models package for the RCA system.
Provides Pydantic models for type-safe data handling throughout the application.
"""

from src.rca.models.conversation import Conversation, ConversationMessage
from src.rca.models.document import Document, DocumentCollection
from src.rca.models.request import RCAQueryRequest
from src.rca.models.response import Citation, ErrorResponse, RCAQueryResponse

__all__ = [
    # Conversation models
    'Conversation',
    'ConversationMessage',
    
    # Document models
    'Document',
    'DocumentCollection',
    
    # API models
    'RCAQueryRequest',
    'RCAQueryResponse',
    'Citation',
    'ErrorResponse',
]
