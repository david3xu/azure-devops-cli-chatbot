"""
Test script for the Azure Search connector using real Azure Search credentials.
This test verifies that the search connector can connect to Azure Search and perform searches.
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env.azure
env_file = os.path.join(Path(__file__).resolve().parent.parent.parent.parent, '.env.azure')
if os.path.exists(env_file):
    print(f"Loading environment from {env_file}")
    load_dotenv(env_file)
else:
    print(f"ERROR: .env.azure file not found at {env_file}")
    sys.exit(1)

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

from src.rca.connectors.embeddings import AzureAdaEmbeddingService
from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

def test_real_search_connector():
    """Test the Azure Search connector using real Azure Search credentials."""
    logger.info("Testing the Azure Search connector with real Azure Search...")
    
    # Initialize the embedding service first
    embedding_service = AzureAdaEmbeddingService()
    
    # Check if embedding service is using mock mode
    if hasattr(embedding_service, 'use_mock') and embedding_service.use_mock:
        logger.warning("Embedding service is using mock mode. Check credentials.")
        print("⚠️ WARNING: Embedding service is in MOCK mode. Real search testing may not work properly.")
    
    # Initialize the search connector
    start_time = time.time()
    search_connector = AzureSearchConnector()  # No parameters needed
    init_time = time.time() - start_time
    
    # Check if search connector is using mock mode
    if hasattr(search_connector, 'use_mock') and search_connector.use_mock:
        logger.warning("Search connector is using mock mode. Check credentials.")
        print("⚠️ WARNING: Search connector is in MOCK mode. Using simulated search results.")
        return False
    
    logger.info(f"Search connector initialized in {init_time:.2f}s")
    print(f"✅ Search connector successfully connected to Azure Search")
    
    # Get search service details if available
    search_service = os.getenv("AZURE_SEARCH_SERVICE", "unknown")
    search_index = os.getenv("AZURE_SEARCH_INDEX", "unknown")
    print(f"   Service: {search_service}")
    print(f"   Index: {search_index}")
    
    # Test queries
    test_queries = [
        "What is Azure DevOps?",
        "How to create a pipeline in Azure DevOps?",
        "Troubleshooting build failures in Azure Pipelines",
        "Azure DevOps best practices for large teams"
    ]
    
    # Test vector search
    print("\nTesting vector search:")
    for query in test_queries:
        start_time = time.time()
        results = search_connector.vector_search(query, top_k=3)
        search_time = time.time() - start_time
        
        print(f"Query: '{query}'")
        print(f"  ↳ Search time: {search_time:.2f}s")
        print(f"  ↳ Results count: {len(results)}")
        
        if len(results) > 0:
            print(f"  ↳ Top result: {results[0]['id'] if 'id' in results[0] else 'unknown'}")
            print(f"  ↳ Score: {results[0]['score'] if 'score' in results[0] else 'unknown'}")
            content_preview = results[0]['content'][:100] + "..." if 'content' in results[0] and len(results[0]['content']) > 100 else results[0].get('content', 'No content')
            print(f"  ↳ Content preview: {content_preview}")
        print()
    
    # Test semantic search
    print("\nTesting semantic search:")
    for query in test_queries[:1]:  # Just test the first query for brevity
        start_time = time.time()
        results = search_connector.semantic_search(query, top_k=3)
        search_time = time.time() - start_time
        
        print(f"Query: '{query}'")
        print(f"  ↳ Search time: {search_time:.2f}s")
        print(f"  ↳ Results count: {len(results)}")
        
        if len(results) > 0:
            print(f"  ↳ Top result: {results[0]['id'] if 'id' in results[0] else 'unknown'}")
            print(f"  ↳ Score: {results[0]['score'] if 'score' in results[0] else 'unknown'}")
            if 'caption' in results[0]:
                print(f"  ↳ Caption: {results[0]['caption']}")
            content_preview = results[0]['content'][:100] + "..." if 'content' in results[0] and len(results[0]['content']) > 100 else results[0].get('content', 'No content')
            print(f"  ↳ Content preview: {content_preview}")
        print()
    
    # Test hybrid search
    print("\nTesting hybrid search:")
    for query in test_queries[:1]:  # Just test the first query for brevity
        start_time = time.time()
        results = search_connector.hybrid_search(query, top_k=3)
        search_time = time.time() - start_time
        
        print(f"Query: '{query}'")
        print(f"  ↳ Search time: {search_time:.2f}s")
        print(f"  ↳ Results count: {len(results)}")
        
        if len(results) > 0:
            print(f"  ↳ Top result: {results[0]['id'] if 'id' in results[0] else 'unknown'}")
            print(f"  ↳ Score: {results[0]['score'] if 'score' in results[0] else 'unknown'}")
            if 'caption' in results[0]:
                print(f"  ↳ Caption: {results[0]['caption']}")
            content_preview = results[0]['content'][:100] + "..." if 'content' in results[0] and len(results[0]['content']) > 100 else results[0].get('content', 'No content')
            print(f"  ↳ Content preview: {content_preview}")
        print()
    
    print("\n✅ Search connector test completed successfully with real Azure Search")
    return True

if __name__ == "__main__":
    print("\n=== Testing Real Azure Search Connector ===\n")
    success = test_real_search_connector()
    if not success:
        print("\n⚠️ Test completed but used mock data instead of real search")
        print("Please check your Azure Search credentials and connectivity")
    print("\n=== Test Completed ===") 