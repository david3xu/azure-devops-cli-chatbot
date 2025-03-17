"""
Comprehensive backward compatibility tests for the RCAAgent class.
These tests verify that all public interfaces remain stable when implementing Milestone 2 features.
Uses actual Azure services to provide real-world validation.
"""
import os
import sys
import time
from pathlib import Path
import unittest
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from src.rca.agents.base_agent import RCAAgent, AgentState
from src.rca.tracking.workflow import WorkflowTracker
from src.rca.tools.search_tools import VectorSearchTool
from src.rca.tools.document_tools import DocumentRankingTool
from src.rca.tools.response_tools import ResponseGenerationTool
from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.connectors.azure_openai import AzureOpenAIConnector
from src.rca.connectors.embeddings import AzureAdaEmbeddingService


class TestRCAAgentBackwardCompatibility(unittest.TestCase):
    """Test suite for ensuring RCAAgent backward compatibility with real Azure services"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment with real Azure services"""
        # Load environment variables from .env.azure file
        env_file = os.path.join(project_root, ".env.azure")
        if os.path.exists(env_file):
            print(f"Loading environment from {env_file}")
            load_dotenv(env_file)
        else:
            print("Warning: .env.azure file not found")
            
        # Initialize real connectors
        cls.search_connector = AzureSearchConnector()
        cls.openai_connector = AzureOpenAIConnector()
        cls.embedding_service = AzureAdaEmbeddingService()
        
        # Verify connectivity to Azure services
        try:
            search_connection_test = cls.search_connector.service_name
            print(f"Successfully connected to Azure Search service: {search_connection_test}")
        except Exception as e:
            print(f"WARNING: Failed to connect to Azure Search: {str(e)}")
            
        try:
            # Simple embedding test to verify OpenAI connectivity
            test_embedding = cls.embedding_service.embed_query("Test query")
            print(f"Successfully connected to Azure OpenAI (embedding dimension: {len(test_embedding)})")
        except Exception as e:
            print(f"WARNING: Failed to connect to Azure OpenAI: {str(e)}")
    
    def setUp(self):
        """Set up test instance with real tools and services"""
        # Create real tools using real connectors
        self.vector_search_tool = VectorSearchTool()
        self.document_ranking_tool = DocumentRankingTool()
        self.response_generation_tool = ResponseGenerationTool()
        
        self.real_tools = {
            "vector_search": self.vector_search_tool,
            "document_ranking": self.document_ranking_tool,
            "response_generation": self.response_generation_tool
        }
        
        self.tracker = WorkflowTracker()
        self.agent = RCAAgent(tools=self.real_tools, tracker=self.tracker)
        
        # Test query to use in tests
        self.test_query = "What is Azure DevOps?"

    def test_init_with_custom_tools(self):
        """Test that agent initializes correctly with custom tools"""
        agent = RCAAgent(tools=self.real_tools)
        self.assertEqual(agent.tools["vector_search"].__class__, VectorSearchTool)
        self.assertEqual(agent.tools["document_ranking"].__class__, DocumentRankingTool)
        self.assertEqual(agent.tools["response_generation"].__class__, ResponseGenerationTool)
        
    def test_init_with_custom_tracker(self):
        """Test that agent initializes correctly with custom tracker"""
        custom_tracker = WorkflowTracker()
        agent = RCAAgent(tracker=custom_tracker)
        self.assertEqual(agent.tracker, custom_tracker)
        
    def test_init_with_defaults(self):
        """Test that agent initializes with default tools when none provided"""
        agent = RCAAgent()
        self.assertIn("vector_search", agent.tools)
        self.assertIn("document_ranking", agent.tools)
        self.assertIn("response_generation", agent.tools)
        self.assertEqual(agent.tools["vector_search"].__class__, VectorSearchTool)

    def test_process_simple_query(self):
        """Test processing a simple query returns expected structure"""
        print(f"\nProcessing query: '{self.test_query}'")
        start_time = time.time()
        
        try:
            result = self.agent.process(self.test_query)
            process_time = time.time() - start_time
            print(f"Query processed in {process_time:.2f} seconds")
            
            # Check the result contains all expected keys
            expected_keys = ["query", "trace_id", "response", "citation_indices", 
                             "documents", "confidence_score"]
            for key in expected_keys:
                self.assertIn(key, result)
                
            # Print summary of results
            print(f"Trace ID: {result['trace_id']}")
            print(f"Retrieved {len(result['documents'])} documents")
            print(f"Response length: {len(result['response'])} characters")
            print(f"Confidence score: {result['confidence_score']}")
            
            # Verify that the response is not empty
            self.assertGreater(len(result["response"]), 0)
            # Verify that documents were retrieved
            self.assertGreater(len(result["documents"]), 0)
            
        except Exception as e:
            self.fail(f"Query processing failed with error: {str(e)}")

    def test_workflow_tracking(self):
        """Test that workflow tracking is called correctly"""
        # Process a query and verify the trace is created
        result = self.agent.process(self.test_query)
        trace_id = result["trace_id"]
        
        # Verify the trace exists and has the correct query
        trace = self.tracker.get_trace(trace_id)
        self.assertIsNotNone(trace)
        self.assertEqual(trace.query, self.test_query)
        
        # Verify there are steps in the trace
        self.assertGreaterEqual(len(trace.steps), 3)  # At least vector search, ranking, and response
        
        # Check for specific steps
        step_names = [step.step_name for step in trace.steps]
        self.assertIn("vector_search", step_names)
        self.assertIn("document_ranking", step_names)
        self.assertIn("response_generation", step_names)

    def test_tool_execution_sequence(self):
        """Test that tools are executed in the correct sequence by examining trace"""
        result = self.agent.process(self.test_query)
        trace_id = result["trace_id"]
        trace = self.tracker.get_trace(trace_id)
        
        # Extract step names
        step_names = [step.step_name for step in trace.steps]
        
        # Verify the sequence of steps
        expected_steps = ["vector_search", "document_ranking", "response_generation"]
        for step in expected_steps:
            self.assertIn(step, step_names)
            
        # Verify order of steps
        vector_index = step_names.index("vector_search")
        ranking_index = step_names.index("document_ranking")
        response_index = step_names.index("response_generation")
        
        self.assertLess(vector_index, ranking_index)
        self.assertLess(ranking_index, response_index)

    def test_error_handling_with_invalid_query(self):
        """Test error handling with an invalid query format"""
        # First check that an invalid query produces some trace data
        try:
            # A short query might work but should have minimal documents at least
            result = self.agent.process("?")
            
            # If no exception, verify we got minimal documents
            trace_id = result["trace_id"]
            trace = self.tracker.get_trace(trace_id)
            self.assertEqual(trace.query, "?")
            
            # Either we get an exception or we get a response with minimal quality
            if "documents" in result:
                print(f"Query '?' returned {len(result['documents'])} documents")
        except Exception as e:
            # If we get an exception, verify it was tracked
            print(f"Query '?' raised exception: {str(e)}")
            traces = self.tracker.get_recent_traces(limit=1)
            latest_trace = traces[0] if traces else None
            
            if latest_trace and hasattr(latest_trace, 'steps'):
                error_steps = [step for step in latest_trace.steps if step.step_name == "error"]
                self.assertGreaterEqual(len(error_steps), 1)

    def test_error_handling_with_forced_error(self):
        """Test error handling with a forced error by temporarily breaking a connector"""
        # Create a copy of the vector search tool with an error
        original_execute = self.vector_search_tool.execute
        
        def mock_execute_with_error(**kwargs):
            """Force an error for testing"""
            raise ValueError("This is a forced test error")
        
        try:
            # Patch the execute method to raise an error
            self.vector_search_tool.execute = mock_execute_with_error
            
            # Process should now raise an exception
            with self.assertRaises(ValueError):
                self.agent.process(self.test_query)
            
            # Verify error was tracked
            traces = self.tracker.get_recent_traces(limit=1)
            latest_trace = traces[0] if traces else None
            
            self.assertIsNotNone(latest_trace)
            if latest_trace:
                error_steps = [step for step in latest_trace.steps if step.step_name == "error"]
                self.assertGreaterEqual(len(error_steps), 1)
                
                # Check error metadata
                for step in error_steps:
                    self.assertEqual(step.metadata.get("error_type"), "ValueError")
                    self.assertIn("This is a forced test error", step.outputs.get("error", ""))
        
        finally:
            # Restore the original execute method
            self.vector_search_tool.execute = original_execute

    def test_tools_can_be_extended(self):
        """Test that additional tools can be added to the agent"""
        # Create a custom tool class for testing
        class CustomTool(VectorSearchTool):
            """Custom tool for testing extensibility"""
            def _execute(self, input_data):
                result = super()._execute(input_data)
                result["custom_field"] = "custom value"
                return result
        
        # Create extended tools dictionary
        custom_tool = CustomTool()
        extended_tools = {**self.real_tools, "custom_tool": custom_tool}
        
        # Create agent with extended tools
        agent = RCAAgent(tools=extended_tools)
        self.assertIn("custom_tool", agent.tools)
        self.assertEqual(agent.tools["custom_tool"], custom_tool)


if __name__ == "__main__":
    unittest.main() 