"""
Test error handling in the RCA system.
Verifies that components properly handle errors and provide fallback functionality.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

from src.rca.connectors.embeddings import AzureAdaEmbeddingService
from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

class TestErrorHandling:
    """Tests for error handling in the RCA system."""
    
    def setup(self):
        """Set up test environment."""
        logger.info("Setting up error handling tests")
        # Intentionally not setting environment variables to test error handling
    
    def test_embedding_service_missing_credentials(self):
        """Test embedding service with missing credentials."""
        logger.info("Testing embedding service with missing credentials")
        
        # Test with no credentials
        with patch.dict(os.environ, {}, clear=True):
            # Use a mock logger to capture log messages
            with patch('src.rca.utils.logging.logging.Logger.warning') as mock_warning:
                embedding_service = AzureAdaEmbeddingService()
                mock_warning.assert_called()
                # Verify service still provides embeddings
                embedding = embedding_service.embed_query("Test query")
                assert len(embedding) == 1536, "Mock embedding should have dimension 1536"
    
    @patch('src.rca.connectors.embeddings.AzureAdaEmbeddingService._call_embedding_api')
    def test_embedding_service_api_errors(self, mock_call_api):
        """Test error handling during embedding API calls."""
        logger.info("Testing embedding service API error handling")
        
        # Mock API to raise an exception
        mock_call_api.side_effect = Exception("API error")
        
        # Setup embedding service 
        embedding_service = AzureAdaEmbeddingService()
        
        # Test single embedding with API error
        embedding = embedding_service.embed_query("Test query")
        assert len(embedding) == 1536, "Should return mock embedding with correct dimension"
        
        # Test batch embedding with API error
        embeddings = embedding_service.embed_documents(["Test doc 1", "Test doc 2"])
        assert len(embeddings) == 2, "Should return correct number of mock embeddings"
        assert all(len(emb) == 1536 for emb in embeddings), "All mock embeddings should have correct dimension"
    
    def test_search_connector_missing_credentials(self):
        """Test search connector with missing credentials."""
        logger.info("Testing search connector with missing credentials")
        
        # Test with no credentials
        with patch.dict(os.environ, {}, clear=True):
            # Use a mock logger to capture log messages
            with patch('src.rca.utils.logging.logging.Logger.warning') as mock_warning:
                # Create mock embedding service
                mock_embedding_service = MagicMock()
                mock_embedding_service.embed_query.return_value = [0.0] * 1536
                
                # Initialize search connector
                search_connector = AzureSearchConnector(embedding_service=mock_embedding_service)
                mock_warning.assert_called()
                
                # Verify service still performs searches
                results = search_connector.vector_search("Test query", top_k=3)
                assert len(results) > 0, "Should return mock search results"
    
    @patch('requests.post')
    def test_search_connector_api_errors(self, mock_post):
        """Test error handling during search API calls."""
        logger.info("Testing search connector API error handling")
        
        # Mock API to return an error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        # Setup with mock embedding service 
        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_query.return_value = [0.0] * 1536
        
        # Initialize search connector and force real API usage for testing
        search_connector = AzureSearchConnector(embedding_service=mock_embedding_service)
        search_connector.use_mock = False  
        
        # Use a mock logger to capture warning messages
        with patch('src.rca.utils.logging.logging.Logger.warning') as mock_warning:
            # Test vector search with API error
            results = search_connector.vector_search("Test query", top_k=3)
            assert len(results) > 0, "Should return mock results on API error"
            mock_warning.assert_called()
    
    def test_end_to_end_error_recovery(self):
        """Test end-to-end error recovery."""
        logger.info("Testing end-to-end error recovery")
        
        # Initialize components without environment variables
        with patch.dict(os.environ, {}, clear=True):
            embedding_service = AzureAdaEmbeddingService()
            search_connector = AzureSearchConnector(embedding_service=embedding_service)
            
            # Test query
            query = "How to set up Azure DevOps?"
            
            # Generate embedding
            embedding = embedding_service.embed_query(query)
            assert len(embedding) == 1536, "Should return mock embedding with correct dimension"
            
            # Perform search
            vector_results = search_connector.vector_search(query, top_k=3)
            assert len(vector_results) > 0, "Should return mock search results"
            
            semantic_results = search_connector.semantic_search(query, top_k=3)
            assert len(semantic_results) > 0, "Should return mock search results"
            
            hybrid_results = search_connector.hybrid_search(query, top_k=3)
            assert len(hybrid_results) > 0, "Should return mock search results"
            
            # Verify that the system can function without access to real services
            logger.info("End-to-end error recovery test completed successfully")

def run_tests():
    """Run the error handling tests."""
    print("\n=== Starting Error Handling Tests ===\n")
    
    test_runner = TestErrorHandling()
    test_runner.setup()
    
    print("\n--- Testing Embedding Service Missing Credentials ---\n")
    test_runner.test_embedding_service_missing_credentials()
    
    print("\n--- Testing Embedding Service API Errors ---\n")
    test_runner.test_embedding_service_api_errors()
    
    print("\n--- Testing Search Connector Missing Credentials ---\n")
    test_runner.test_search_connector_missing_credentials()
    
    print("\n--- Testing Search Connector API Errors ---\n")
    test_runner.test_search_connector_api_errors()
    
    print("\n--- Testing End-to-End Error Recovery ---\n")
    test_runner.test_end_to_end_error_recovery()
    
    print("\n=== All Error Handling Tests Completed Successfully ===\n")

if __name__ == "__main__":
    run_tests() 