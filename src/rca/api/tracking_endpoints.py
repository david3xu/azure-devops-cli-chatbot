"""
API endpoints for workflow tracking.
Provides access to workflow execution traces.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional

from src.rca.tracking.workflow import WorkflowTracker, WorkflowTrace
from src.rca.agents.base_agent import RCAAgent


# Create router
router = APIRouter(
    prefix="/rca/tracking",
    tags=["workflow-tracking"],
)


def get_tracker():
    """Dependency to get the workflow tracker from the agent"""
    agent = RCAAgent()
    return agent.tracker


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str, tracker: WorkflowTracker = Depends(get_tracker)):
    """
    Get detailed information for a specific workflow trace
    
    Args:
        trace_id: The ID of the trace to retrieve
        tracker: The workflow tracker instance
        
    Returns:
        Complete trace information
    """
    trace = tracker.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    return trace


@router.get("/traces")
async def list_traces(limit: int = 10, tracker: WorkflowTracker = Depends(get_tracker)):
    """
    List recent workflow traces
    
    Args:
        limit: Maximum number of traces to return
        tracker: The workflow tracker instance
        
    Returns:
        List of recent traces
    """
    traces = tracker.get_recent_traces(limit=limit)
    return traces 