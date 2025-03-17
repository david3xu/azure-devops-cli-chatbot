"""
Integration tests for the full RAG pipeline.
Tests the complete flow from embedding generation to search to result handling.
"""
import os
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from src.rca.connectors.embeddings import AzureAdaEmbeddingService
from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.tools.search_tools import VectorSearchTool, SemanticSearchTool, HybridSearchTool
from src.rca.models.conversation import Conversation, ConversationMessage
from src.rca.utils.evaluation import SearchEvaluator
from src.rca.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

class TestRAGPipeline:
    """Integration tests for the full RAG pipeline."""
    
    def setup(self):
        """Set up the test environment."""
        logger.info("Setting up RAG pipeline integration test")
        self.embedding_service = AzureAdaEmbeddingService()
        self.search_connector = AzureSearchConnector(embedding_service=self.embedding_service)
        
        # Initialize tools
        self.vector_search_tool = VectorSearchTool(search_connector=self.search_connector)
        self.semantic_search_tool = SemanticSearchTool(search_connector=self.search_connector)
        self.hybrid_search_tool = HybridSearchTool(search_connector=self.search_connector)
        
        # Initialize conversation
        self.conversation = Conversation(
            system_prompt="You are a helpful assistant that answers Azure DevOps questions.",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Initialize evaluator
        self.evaluator = SearchEvaluator()
        
    def test_full_pipeline_with_mock_data(self):
        """Test the full RAG pipeline with mock data."""
        self.setup()
        
        # Test query
        query = "What is the best way to troubleshoot Azure DevOps pipeline failures?"
        
        # Step 1: Generate embedding for the query
        logger.info("Step 1: Generating embedding for query")
        start_time = time.time()
        query_embedding = self.embedding_service.embed_query(query)
        embedding_time = time.time() - start_time
        logger.info(f"Query embedding generated in {embedding_time:.2f} seconds")
        
        # Verify embedding
        assert len(query_embedding) == 1536, f"Expected embedding dimension 1536, got {len(query_embedding)}"
        
        # Step 2: Perform searches
        logger.info("Step 2: Performing searches")
        
        # Vector search
        start_time = time.time()
        vector_results = self.vector_search_tool.execute(query=query, top_k=3)
        vector_time = time.time() - start_time
        logger.info(f"Vector search completed in {vector_time:.2f} seconds")
        
        # Semantic search
        start_time = time.time()
        semantic_results = self.semantic_search_tool.execute(query=query, top_k=3)
        semantic_time = time.time() - start_time
        logger.info(f"Semantic search completed in {semantic_time:.2f} seconds")
        
        # Hybrid search
        start_time = time.time()
        hybrid_results = self.hybrid_search_tool.execute(query=query, top_k=3)
        hybrid_time = time.time() - start_time
        logger.info(f"Hybrid search completed in {hybrid_time:.2f} seconds")
        
        # Verify results format
        assert "results" in vector_results, "Vector search results missing 'results' key"
        assert "results" in semantic_results, "Semantic search results missing 'results' key"
        assert "results" in hybrid_results, "Hybrid search results missing 'results' key"
        
        # Verify result counts
        assert len(vector_results["results"]) <= 3, f"Expected ≤3 vector results, got {len(vector_results['results'])}"
        assert len(semantic_results["results"]) <= 3, f"Expected ≤3 semantic results, got {len(semantic_results['results'])}"
        assert len(hybrid_results["results"]) <= 3, f"Expected ≤3 hybrid results, got {len(hybrid_results['results'])}"
        
        # Step 3: Add results to conversation
        logger.info("Step 3: Adding results to conversation")
        
        # Combine results (in real scenario you might use one type or rerank)
        all_results = []
        for result in vector_results["results"]:
            if result not in all_results:
                all_results.append(result)
                
        for result in semantic_results["results"]:
            if result not in all_results:
                all_results.append(result)
                
        for result in hybrid_results["results"]:
            if result not in all_results:
                all_results.append(result)
        
        # Format context from results
        context = "\n\n".join([f"Document: {result['content']}" for result in all_results])
        
        # Add user query to conversation
        self.conversation.add_message(
            role="user",
            content=query
        )
        
        # In a real system, the context would be passed to an LLM along with the conversation
        # For this test, we'll simulate the assistant response
        simulated_response = (
            "To troubleshoot Azure DevOps pipeline failures, follow these steps:\n\n"
            "1. Check the pipeline logs for error messages\n"
            "2. Review recent changes to your code and pipeline configuration\n"
            "3. Validate your build agents are functioning correctly\n"
            "4. Check for service outages in Azure DevOps\n"
            "5. Test problematic steps locally if possible"
        )
        
        # Add assistant response to conversation
        self.conversation.add_message(
            role="assistant",
            content=simulated_response
        )
        
        # Verify conversation state
        messages = self.conversation.messages
        assert len(messages) == 3, f"Expected 3 messages in conversation, got {len(messages)}"
        assert messages[0].role == "system", "First message should be system prompt"
        assert messages[1].role == "user", "Second message should be user query"
        assert messages[2].role == "assistant", "Third message should be assistant response"
        
        # Step 4: Evaluate search quality
        logger.info("Step 4: Evaluating search quality")
        
        # Define expected documents (in a real test, these would be from a test dataset)
        expected_docs = [result["id"] for result in all_results[:2]]  # Assume top 2 are relevant
        
        # Evaluate each search method
        vector_metrics = self.evaluator.evaluate_search_results(
            query=query,
            results=[r["id"] for r in vector_results["results"]],
            expected_docs=expected_docs,
            latency=vector_time
        )
        
        semantic_metrics = self.evaluator.evaluate_search_results(
            query=query,
            results=[r["id"] for r in semantic_results["results"]],
            expected_docs=expected_docs,
            latency=semantic_time
        )
        
        hybrid_metrics = self.evaluator.evaluate_search_results(
            query=query,
            results=[r["id"] for r in hybrid_results["results"]],
            expected_docs=expected_docs,
            latency=hybrid_time
        )
        
        # Log metrics
        logger.info(f"Vector search metrics: {vector_metrics}")
        logger.info(f"Semantic search metrics: {semantic_metrics}")
        logger.info(f"Hybrid search metrics: {hybrid_metrics}")
        
        # Verification complete
        logger.info("RAG pipeline integration test completed successfully")
        
    def test_toggle_between_mock_and_real(self):
        """Test toggling between mock and real services."""
        self.setup()
        
        # Check initial state
        initial_mock_state = self.search_connector.use_mock
        logger.info(f"Initial mock state: {initial_mock_state}")
        
        # Test query
        query = "How to create a build pipeline in Azure DevOps?"
        
        # Force mock mode on
        self.search_connector.use_mock = True
        mock_results = self.vector_search_tool.execute(query=query, top_k=3)
        assert "results" in mock_results, "Mock results should contain 'results' key"
        assert len(mock_results["results"]) > 0, "Mock results should not be empty"
        
        # In a real scenario with valid Azure credentials, we would test switching to real mode
        # For this test, we'll just verify we can toggle the flag
        prev_state = self.search_connector.use_mock
        self.search_connector.use_mock = not prev_state
        assert self.search_connector.use_mock != prev_state, "Mock state should have toggled"
        
        # Reset state
        self.search_connector.use_mock = initial_mock_state
        
def run_tests():
    """Run the integration tests."""
    print("\n=== Starting RAG Pipeline Integration Tests ===\n")
    
    test_runner = TestRAGPipeline()
    
    print("\n--- Testing Full Pipeline with Mock Data ---\n")
    test_runner.test_full_pipeline_with_mock_data()
    
    print("\n--- Testing Toggle Between Mock and Real Services ---\n")
    test_runner.test_toggle_between_mock_and_real()
    
    print("\n=== All Integration Tests Completed Successfully ===\n")

if __name__ == "__main__":
    run_tests() 