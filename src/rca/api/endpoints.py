"""
API endpoints for the RCA system.
Provides FastAPI endpoints for querying the RCA system.
"""
from fastapi import APIRouter, HTTPException, Depends
import time
import uuid
from typing import Dict, List, Optional, Any

from src.rca.agents.base_agent import RCAAgent
from src.rca.models.request import RCAQueryRequest, FeedbackRequest
from src.rca.models.response import RCAQueryResponse, ErrorResponse


# Create router
router = APIRouter(
    prefix="/rca",
    tags=["root-cause-analysis"],
    responses={404: {"model": ErrorResponse}}
)


def get_agent():
    """Dependency to get a configured RCA agent."""
    return RCAAgent()


@router.post("/query", response_model=RCAQueryResponse)
async def query(request: RCAQueryRequest, agent: RCAAgent = Depends(get_agent)):
    """
    Process a query using the RCA system.
    
    Args:
        request: Query request
        agent: RCA agent instance
        
    Returns:
        Query response
    """
    try:
        # Track processing time
        start_time = time.time()
        
        # Process query
        result = agent.process(request.query)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Create response
        return RCAQueryResponse(
            query_id=result.get("query_id", str(uuid.uuid4())),
            response=result["response"],
            citations=[{"document_id": f"doc{i+1}"} for i in result["citation_indices"]],
            confidence_score=result.get("confidence_score", 0.0),
            processing_time_ms=processing_time_ms,
            metadata={"user_id": request.user_id} if request.user_id else {}
        )
    except Exception as e:
        # Log error and return error response
        print(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback", response_model=Dict[str, str])
async def feedback(request: FeedbackRequest):
    """
    Submit feedback for a query.
    
    Args:
        request: Feedback request
        
    Returns:
        Acknowledgement
    """
    try:
        # In a real implementation, store feedback in a database
        print(f"Received feedback for query {request.query_id}: rating={request.rating}")
        
        return {"status": "success", "message": "Feedback received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 