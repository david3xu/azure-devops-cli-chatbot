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
    """Track workflow execution with inputs and outputs at each step"""
    
    def __init__(self):
        self.active_traces: Dict[str, WorkflowTrace] = {}
        self.completed_traces: List[WorkflowTrace] = []
        self.storage_backends = []
        
        # Add file storage backend by default
        self.register_storage_backend(FileStorageBackend())
        
        # Load existing traces on startup
        self._load_traces_from_storage()
    
    def _load_traces_from_storage(self):
        """Load traces from storage backends"""
        for backend in self.storage_backends:
            if hasattr(backend, 'load_traces'):
                traces = backend.load_traces()
                self.completed_traces.extend(traces)
                print(f"Loaded {len(traces)} traces from storage")
    
    def register_storage_backend(self, backend):
        """Register a storage backend for traces"""
        self.storage_backends.append(backend)
    
    def start_trace(self, query: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start tracking a new workflow execution"""
        trace = WorkflowTrace(
            query=query,
            metadata=metadata or {}
        )
        self.active_traces[trace.trace_id] = trace
        return trace.trace_id
    
    def track_step(self, trace_id: str, step_name: str, 
                  inputs: Dict[str, Any], outputs: Dict[str, Any],
                  metadata: Optional[Dict[str, Any]] = None) -> None:
        """Track a step in the workflow"""
        if trace_id not in self.active_traces:
            return
            
        trace = self.active_traces[trace_id]
        step = trace.add_step(step_name, inputs)
        if metadata:
            step.metadata = metadata
        trace.complete_step(step, outputs)
    
    def complete_trace(self, trace_id: str, final_response: str) -> Optional[WorkflowTrace]:
        """Complete a workflow trace"""
        if trace_id not in self.active_traces:
            return None
            
        trace = self.active_traces.pop(trace_id)
        trace.complete_workflow(final_response)
        
        # Store the completed trace
        self.completed_traces.append(trace)
        for backend in self.storage_backends:
            backend.store_trace(trace)
            
        return trace
    
    def get_trace(self, trace_id: str) -> Optional[WorkflowTrace]:
        """Get a trace by ID"""
        if trace_id in self.active_traces:
            return self.active_traces[trace_id]
            
        for trace in self.completed_traces:
            if trace.trace_id == trace_id:
                return trace
                
        return None
    
    def get_recent_traces(self, limit: int = 10) -> List[WorkflowTrace]:
        """Get the most recent traces"""
        return self.completed_traces[-limit:] 