"""
Response models for the RCA system API.
Defines the structure of outgoing responses.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class Citation(BaseModel):
    """
    Citation for a document used in the response.
    """
    document_id: str
    start_index: Optional[int] = None
    end_index: Optional[int] = None


class RCAQueryResponse(BaseModel):
    """
    Response model for RCA query API.
    """
    query_id: str
    response: str
    citations: List[Citation] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    processing_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """
    Response model for errors.
    """
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None 