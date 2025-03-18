"""
Visualization endpoints for workflow tracking.
Provides HTML views of workflow execution traces.
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from src.rca.tracking.workflow import WorkflowTracker
from src.rca.agents.base_agent import RCAAgent


# Create router
router = APIRouter(
    prefix="/rca/visualize",
    tags=["visualization"],
)


# Set up templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)


def get_tracker():
    """Dependency to get the workflow tracker from the agent"""
    agent = RCAAgent()
    # Make sure the tracker is using the correct storage path
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    storage_dir = os.path.join(base_dir, 'data', 'traces')
    print(f"Using trace storage directory: {storage_dir}")
    # Replace the tracker's storage backend
    from src.rca.tracking.workflow import FileStorageBackend
    agent.tracker.register_storage_backend(FileStorageBackend(storage_dir))
    return agent.tracker


@router.get("/trace/{trace_id}", response_class=HTMLResponse)
async def visualize_trace(
    request: Request, 
    trace_id: str, 
    tracker: WorkflowTracker = Depends(get_tracker)
):
    """
    Visualize a single workflow trace
    
    Args:
        request: The FastAPI request
        trace_id: The ID of the trace to visualize
        tracker: The workflow tracker instance
        
    Returns:
        HTML visualization of the trace
    """
    trace = tracker.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    return templates.TemplateResponse("trace.html", {
        "request": request,
        "trace": trace
    })


@router.get("/traces", response_class=HTMLResponse)
async def visualize_traces(
    request: Request, 
    limit: int = 10,
    tracker: WorkflowTracker = Depends(get_tracker)
):
    """
    Visualize all recent traces
    
    Args:
        request: The FastAPI request
        limit: Maximum number of traces to show
        tracker: The workflow tracker instance
        
    Returns:
        HTML visualization of the traces
    """
    traces = tracker.get_recent_traces(limit=limit)
    
    return templates.TemplateResponse("traces.html", {
        "request": request,
        "traces": traces
    }) 