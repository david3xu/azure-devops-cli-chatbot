"""
Request models for the RCA system API.
Defines the structure of incoming requests.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class RCAQueryRequest(BaseModel):
    """
    Request model for RCA query API.
    """
    query: str
    max_documents: Optional[int] = 5
    temperature: Optional[float] = 0.7
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeedbackRequest(BaseModel):
    """
    Request model for providing feedback on RCA responses.
    """
    query_id: str
    rating: int
    comments: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict) 