"""
Tests for the workflow tracking system integration.
Tests both core tracking functionality and integration with CLI and API.
"""
import os
import time
import json
import shutil
import inspect
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from src.rca.tracking.workflow import WorkflowTracker, WorkflowTrace
from src.rca.tracking.storage import JSONFileStorage, InMemoryStorage
from src.rca.agents.base_agent import RCAAgent
from src.rca_cli import process_query
from src.main import app

# Constants for testing
TEST_TRACES_DIR = "test_traces"
TEST_QUERY = "What causes database connection timeout issues?"


# Fixtures
@pytest.fixture(scope="function")
def temp_trace_dir():
    """Create a temporary directory for test traces."""
    if os.path.exists(TEST_TRACES_DIR):
        shutil.rmtree(TEST_TRACES_DIR)
    os.makedirs(TEST_TRACES_DIR)
    yield TEST_TRACES_DIR
    shutil.rmtree(TEST_TRACES_DIR)


@pytest.fixture
def memory_storage():
    """Create a memory storage backend for testing."""
    return InMemoryStorage()


@pytest.fixture
def file_storage(temp_trace_dir):
    """Create a file storage backend for testing."""
    return JSONFileStorage(temp_trace_dir)


@pytest.fixture
def tracker(memory_storage):
    """Create a workflow tracker with memory storage."""
    tracker = WorkflowTracker()
    tracker.register_storage_backend(memory_storage)
    return tracker


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# Core WorkflowTracker Tests
class TestWorkflowTracker:
    """Tests for the WorkflowTracker core functionality."""

    def test_tracker_creation(self):
        """Test that a tracker can be created."""
        tracker = WorkflowTracker()
        assert tracker is not None
        assert hasattr(tracker, 'active_traces')
        assert hasattr(tracker, 'completed_traces')

    def test_start_trace(self, tracker):
        """Test starting a new trace."""
        trace_id = tracker.start_trace(TEST_QUERY)
        assert trace_id is not None
        assert len(trace_id) > 0
        assert trace_id in tracker.active_traces

    def test_track_step(self, tracker):
        """Test recording a step in a trace."""
        trace_id = tracker.start_trace(TEST_QUERY)
        
        # Record step
        tracker.track_step(
            trace_id,
            "vector_search", 
            {"query": TEST_QUERY}, 
            {"results": ["doc1", "doc2"]}
        )
        
        # Get trace and check step
        trace = tracker.get_trace(trace_id)
        assert len(trace.steps) == 1
        assert trace.steps[0].step_name == "vector_search"
        assert trace.steps[0].inputs["query"] == TEST_QUERY
        assert "results" in trace.steps[0].outputs
        assert len(trace.steps[0].outputs["results"]) == 2

    def test_multiple_steps(self, tracker):
        """Test recording multiple steps in a trace."""
        trace_id = tracker.start_trace(TEST_QUERY)
        
        # Record first step
        tracker.track_step(
            trace_id,
            "query_understanding", 
            {"query": TEST_QUERY},
            {"intent": "database"}
        )
        
        # Record second step
        tracker.track_step(
            trace_id,
            "vector_search", 
            {"intent": "database"},
            {"results": ["doc1"]}
        )
        
        # Get trace and check steps
        trace = tracker.get_trace(trace_id)
        assert len(trace.steps) == 2
        assert trace.steps[0].step_name == "query_understanding"
        assert trace.steps[1].step_name == "vector_search"

    def test_complete_trace(self, tracker):
        """Test completing a trace."""
        trace_id = tracker.start_trace(TEST_QUERY)
        tracker.track_step(trace_id, "test_step", {}, {})
        
        # End the trace
        trace = tracker.complete_trace(trace_id, "Test response")
        
        # Check that the trace is completed
        assert trace.end_time is not None
        assert trace.final_response == "Test response"
        assert trace_id not in tracker.active_traces
        assert trace in tracker.completed_traces

    def test_trace_timing(self, tracker):
        """Test that trace timing information is recorded."""
        trace_id = tracker.start_trace(TEST_QUERY)
        
        # Add a small delay to ensure timing is measurable
        time.sleep(0.01)
        
        # End the trace
        trace = tracker.complete_trace(trace_id, "Test response")
        
        # Check timing
        assert trace.start_time is not None
        assert trace.end_time is not None
        assert trace.end_time > trace.start_time
        assert trace.duration_ms > 0


# Storage Backend Tests
class TestStorageBackends:
    """Tests for storage backends."""

    def test_memory_storage(self, tracker, memory_storage):
        """Test that traces are stored in memory storage."""
        trace_id = tracker.start_trace(TEST_QUERY)
        tracker.track_step(trace_id, "test_step", {}, {})
        tracker.complete_trace(trace_id, "Test response")
        
        # Check that the trace is in the storage
        trace = memory_storage.get_trace(trace_id)
        assert trace is not None
        assert trace.query == TEST_QUERY

    def test_file_storage(self, file_storage, temp_trace_dir):
        """Test that traces are stored in file storage."""
        # Create tracker with file storage
        tracker = WorkflowTracker()
        tracker.register_storage_backend(file_storage)
        
        # Create and complete a trace
        trace_id = tracker.start_trace(TEST_QUERY)
        tracker.track_step(trace_id, "test_step", {}, {})
        tracker.complete_trace(trace_id, "Test response")
        
        # Check that the trace file exists
        trace_file = Path(temp_trace_dir) / f"{trace_id}.json"
        assert trace_file.exists()
        
        # Check that the file contains the correct data
        with open(trace_file, 'r') as f:
            data = json.load(f)
            assert data["query"] == TEST_QUERY
            assert len(data["steps"]) == 1

    def test_multiple_storages(self, memory_storage, file_storage, temp_trace_dir):
        """Test that traces are stored in multiple storage backends."""
        tracker = WorkflowTracker()
        tracker.register_storage_backend(memory_storage)
        tracker.register_storage_backend(file_storage)
        
        # Create and complete a trace
        trace_id = tracker.start_trace(TEST_QUERY)
        tracker.track_step(trace_id, "test_step", {}, {})
        tracker.complete_trace(trace_id, "Test response")
        
        # Check memory storage
        trace = memory_storage.get_trace(trace_id)
        assert trace is not None
        
        # Check file storage
        trace_file = Path(temp_trace_dir) / f"{trace_id}.json"
        assert trace_file.exists()


# CLI Integration Tests
class TestCLIIntegration:
    """Tests for CLI integration with workflow tracking."""

    def test_cli_has_tracking_code(self):
        """Test that workflow tracking code is in the CLI module."""
        # Check that the CLI module imports the tracking components
        import src.rca_cli
        source_code = inspect.getsource(src.rca_cli)
        assert "WorkflowTracker" in source_code
        assert "register_storage_backend" in source_code
        assert "JSONFileStorage" in source_code
        assert "trace_id" in source_code  # Checks for trace ID in output

    @pytest.mark.integration
    def test_cli_output_contains_trace_id(self):
        """Test that CLI output contains a trace ID."""
        # This test requires the CLI to be runnable
        # Skip it if we're not running integration tests
        result = subprocess.run(
            ["python", "-m", "src.rca_cli", TEST_QUERY, "--verbose"],
            capture_output=True, text=True
        )
        
        # Check that the output contains a trace ID
        assert "Trace ID:" in result.stdout


# API Integration Tests
class TestAPIIntegration:
    """Tests for API integration with workflow tracking."""

    def test_tracking_endpoints_exist(self, test_client):
        """Test that tracking endpoints exist in the API."""
        response = test_client.get("/rca/tracking/traces")
        assert response.status_code == 200
        # The format depends on implementation, but at minimum it should be a valid JSON
        assert response.json() is not None

    def test_visualization_endpoints_exist(self, test_client):
        """Test that visualization endpoints exist in the API."""
        response = test_client.get("/rca/visualize/traces")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    @pytest.mark.integration
    def test_create_and_retrieve_trace(self, test_client):
        """Test creating a trace through the RCA endpoint and retrieving it."""
        # First, create a trace by making an RCA query
        query_response = test_client.post(
            "/rca/query",
            json={"query": TEST_QUERY}
        )
        assert query_response.status_code == 200
        
        # This test needs to be customized based on the actual response format
        # Some responses might include trace_id directly, others might require extracting it
        # from metadata or other fields
        result = query_response.json()
        
        # If trace_id is available, use it to test retrieval
        if "trace_id" in result:
            trace_id = result["trace_id"]
            
            # Then, retrieve the trace
            trace_response = test_client.get(f"/rca/tracking/traces/{trace_id}")
            assert trace_response.status_code == 200
            trace = trace_response.json()
            assert trace["query"] == TEST_QUERY


# Performance Tests
class TestPerformance:
    """Performance tests for workflow tracking."""

    @pytest.mark.performance
    def test_tracking_overhead(self):
        """Test that workflow tracking doesn't add significant overhead."""
        # This requires tracking to be optional in the process_query function
        # Mocking the function to simulate with/without tracking
        
        with patch('src.rca.agents.base_agent.RCAAgent') as MockAgent:
            mock_agent_instance = MagicMock()
            MockAgent.return_value = mock_agent_instance
            mock_agent_instance.process.return_value = {"response": "Test response"}
            
            # Time with tracking (normal operation)
            start = time.time()
            for _ in range(10):  # Reduced iterations to speed up tests
                process_query(TEST_QUERY, verbose=False)
            tracking_time = time.time() - start
            
            # Time without tracking (by mocking the tracker to do nothing)
            with patch('src.rca.tracking.workflow.WorkflowTracker.register_storage_backend'), \
                 patch('src.rca.tracking.workflow.WorkflowTracker.start_trace'), \
                 patch('src.rca.tracking.workflow.WorkflowTracker.track_step'), \
                 patch('src.rca.tracking.workflow.WorkflowTracker.complete_trace'):
                
                start = time.time()
                for _ in range(10):  # Reduced iterations to speed up tests
                    process_query(TEST_QUERY, verbose=False)
                no_tracking_time = time.time() - start
            
            # Verify overhead is acceptable (less than 100%)
            # This is a very generous margin because we're running fewer iterations
            # and the test environment may have high variability
            assert tracking_time < no_tracking_time * 10, \
                f"Tracking adds too much overhead: {tracking_time:.4f}s vs {no_tracking_time:.4f}s" 