"""
Workflow tracking system for the RCA pipeline.
Provides tracing of inputs, outputs, and performance for each step.
"""
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import os
import json
import pickle
from pathlib import Path


class StepTrace(BaseModel):
    """Trace information for a single step in the workflow"""
    step_name: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any] 
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowTrace(BaseModel):
    """Complete trace of a workflow execution"""
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    steps: List[StepTrace] = Field(default_factory=list)
    final_response: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_step(self, step_name: str, inputs: Dict[str, Any]) -> StepTrace:
        """Add a new step to the trace"""
        step = StepTrace(
            step_name=step_name,
            inputs=inputs,
            outputs={},
            start_time=datetime.now()
        )
        self.steps.append(step)
        return step
    
    def complete_step(self, step: StepTrace, outputs: Dict[str, Any]):
        """Complete a step with outputs and timing information"""
        step.outputs = outputs
        step.end_time = datetime.now()
        step.duration_ms = (step.end_time - step.start_time).total_seconds() * 1000
    
    def complete_workflow(self, final_response: str):
        """Complete the workflow trace"""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.final_response = final_response


class FileStorageBackend:
    """Simple file-based storage backend for workflow traces"""
    
    def __init__(self, storage_dir=None):
        """Initialize the file storage backend"""
        if storage_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            storage_dir = os.path.join(base_dir, 'data', 'traces')
            
        os.makedirs(storage_dir, exist_ok=True)
        self.storage_dir = storage_dir
        print(f"Trace storage initialized at: {self.storage_dir}")
        
    def store_trace(self, trace: WorkflowTrace):
        """Store a trace to a file"""
        trace_file = os.path.join(self.storage_dir, f"{trace.trace_id}.pkl")
        
        try:
            with open(trace_file, 'wb') as f:
                pickle.dump(trace, f)
            print(f"Stored trace {trace.trace_id} to {trace_file}")
            return True
        except Exception as e:
            print(f"Error storing trace: {str(e)}")
            return False
            
    def load_traces(self, limit=None):
        """Load traces from storage"""
        traces = []
        
        try:
            trace_files = sorted(
                [f for f in os.listdir(self.storage_dir) if f.endswith('.pkl')],
                key=lambda x: os.path.getmtime(os.path.join(self.storage_dir, x)),
                reverse=True
            )
            
            if limit:
                trace_files = trace_files[:limit]
                
            for trace_file in trace_files:
                try:
                    with open(os.path.join(self.storage_dir, trace_file), 'rb') as f:
                        trace = pickle.load(f)
                        traces.append(trace)
                except Exception as e:
                    print(f"Error loading trace {trace_file}: {str(e)}")
            
            return traces
        except Exception as e:
            print(f"Error listing traces: {str(e)}")
            return []


class WorkflowTracker:
    """
    Tracks workflow execution steps and stores traces.
    Provides methods to retrieve and analyze workflow execution.
    """
    
    def __init__(self, storage_backend=None):
        """Initialize the workflow tracker"""
        self.traces = {}
        self.storage_backend = storage_backend or FileStorageBackend()
        self._load_traces()
        
    def _load_traces(self):
        """Load traces from storage"""
        if hasattr(self.storage_backend, 'load_traces'):
            loaded_traces = self.storage_backend.load_traces()
            for trace in loaded_traces:
                self.traces[trace.trace_id] = trace
            print(f"Loaded {len(loaded_traces)} traces from storage")
    
    def register_storage_backend(self, storage_backend):
        """Register a different storage backend"""
        self.storage_backend = storage_backend
        self._load_traces()
        
    def start_trace(self, query):
        """Start a new workflow trace"""
        trace_id = str(uuid.uuid4())
        self.traces[trace_id] = WorkflowTrace(
            trace_id=trace_id,
            query=query,
            start_time=datetime.now()
        )
        print(f"Started new trace {trace_id} for query: {query}")
        return trace_id
        
    def complete_trace(self, trace_id, final_response=None):
        """Complete a workflow trace"""
        if trace_id not in self.traces:
            print(f"Warning: Trace {trace_id} not found in memory")
            return False
            
        trace = self.traces[trace_id]
        trace.end_time = datetime.now()
        trace.duration_ms = (trace.end_time - trace.start_time).total_seconds() * 1000
        
        if final_response is not None:
            trace.final_response = final_response
            
        # Store to persistent storage
        if self.storage_backend:
            self.storage_backend.store_trace(trace)
            
        return True
    
    def track_step(self, trace_id, step_name, inputs, outputs, metadata=None):
        """Track a step in the workflow"""
        if trace_id not in self.traces:
            print(f"Warning: Trace {trace_id} not found for step {step_name}")
            return False
            
        trace = self.traces[trace_id]
        
        # Find existing step with same name or create new one
        existing_steps = [s for s in trace.steps if s.step_name == step_name]
        
        if existing_steps:
            step = existing_steps[0]
            # Update the step
            step.outputs = outputs
            step.end_time = datetime.now()
            step.duration_ms = (step.end_time - step.start_time).total_seconds() * 1000
            if metadata:
                step.metadata.update(metadata)
        else:
            # Create a new step
            step = StepTrace(
                step_name=step_name,
                inputs=inputs,
                outputs=outputs,
                start_time=datetime.now(),
                end_time=datetime.now(),
                metadata=metadata or {}
            )
            trace.steps.append(step)
            
        return True
        
    def get_trace(self, trace_id):
        """Get a specific trace by ID"""
        # Try to get from memory first
        if trace_id in self.traces:
            return self.traces[trace_id]
            
        # Try to load from storage if available
        if hasattr(self.storage_backend, 'get_trace'):
            trace = self.storage_backend.get_trace(trace_id)
            if trace:
                self.traces[trace_id] = trace
                return trace
                
        return None
        
    def get_recent_traces(self, limit=10):
        """Get the most recent traces"""
        # First, ensure we've loaded all available traces
        self._load_traces()
        
        # Get all traces and sort by start_time descending
        all_traces = list(self.traces.values())
        
        # Debug output of trace dates
        for trace in all_traces:
            print(f"Found trace: {trace.trace_id} - {trace.query} - {trace.start_time}")
        
        # Sort by start_time descending (most recent first)
        sorted_traces = sorted(
            all_traces, 
            key=lambda t: t.start_time if t.start_time else datetime.min, 
            reverse=True
        )
        
        # Log the sorting results
        print(f"Returning {min(limit, len(sorted_traces))} traces from {len(sorted_traces)} total")
        for i, trace in enumerate(sorted_traces[:limit]):
            print(f"{i+1}. {trace.trace_id} - {trace.query} - {trace.start_time}")
        
        return sorted_traces[:limit] 