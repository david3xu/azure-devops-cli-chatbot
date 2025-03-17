"""
Storage backends for workflow tracking.
Provides persistence options for workflow trace data.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.rca.tracking.workflow import WorkflowTrace


class BaseStorageBackend:
    """Base class for workflow trace storage backends"""
    
    def store_trace(self, trace: WorkflowTrace) -> None:
        """Store a completed workflow trace"""
        raise NotImplementedError()
    
    def get_trace(self, trace_id: str) -> Optional[WorkflowTrace]:
        """Retrieve a trace by ID"""
        raise NotImplementedError()


class JSONFileStorage(BaseStorageBackend):
    """Store workflow traces as JSON files"""
    
    def __init__(self, directory: str = "traces"):
        """Initialize JSON file storage with the specified directory"""
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
    
    def store_trace(self, trace: WorkflowTrace) -> None:
        """Store a trace as a JSON file"""
        # Convert datetime to strings for JSON serialization
        trace_dict = trace.dict()
        filename = os.path.join(self.directory, f"{trace.trace_id}.json")
        
        with open(filename, "w") as f:
            json.dump(trace_dict, f, indent=2, default=str)
    
    def get_trace(self, trace_id: str) -> Optional[WorkflowTrace]:
        """Retrieve a trace from a JSON file"""
        filename = os.path.join(self.directory, f"{trace_id}.json")
        if not os.path.exists(filename):
            return None
            
        with open(filename, "r") as f:
            trace_dict = json.load(f)
            
        # Convert string times back to datetime
        return WorkflowTrace(**trace_dict)


class InMemoryStorage(BaseStorageBackend):
    """Store workflow traces in memory"""
    
    def __init__(self, max_traces: int = 100):
        """Initialize in-memory storage with a max number of traces to keep"""
        self.traces: Dict[str, WorkflowTrace] = {}
        self.max_traces = max_traces
        self.trace_ids: List[str] = []
    
    def store_trace(self, trace: WorkflowTrace) -> None:
        """Store a trace in memory"""
        self.traces[trace.trace_id] = trace
        self.trace_ids.append(trace.trace_id)
        
        # Remove oldest traces if we exceed max_traces
        if len(self.trace_ids) > self.max_traces:
            oldest_id = self.trace_ids.pop(0)
            self.traces.pop(oldest_id, None)
    
    def get_trace(self, trace_id: str) -> Optional[WorkflowTrace]:
        """Retrieve a trace from memory"""
        return self.traces.get(trace_id)
    
    def get_all_traces(self) -> List[WorkflowTrace]:
        """Get all stored traces"""
        return list(self.traces.values()) 