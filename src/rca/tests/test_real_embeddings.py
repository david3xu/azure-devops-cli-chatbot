"""
Test script for the embedding service using real Azure OpenAI credentials.
This test verifies that the embedding service can connect to Azure OpenAI and generate real embeddings.
"""
import os
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

from src.rca.connectors.embeddings import AzureAdaEmbeddingService
from src.rca.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

def test_real_embedding_service():
    """Test the embedding service using real Azure OpenAI credentials."""
    logger.info("Testing the embedding service with real Azure OpenAI...")
    
    # Initialize the embedding service
    start_time = time.time()
    embedding_service = AzureAdaEmbeddingService()
    init_time = time.time() - start_time
    
    # Check if mock mode is being used
    if hasattr(embedding_service, 'use_mock') and embedding_service.use_mock:
        logger.warning("Embedding service is using mock mode. Check credentials.")
        print("⚠️ WARNING: Embedding service is in MOCK mode. Using simulated embeddings.")
        return False
    
    logger.info(f"Embedding service initialized in {init_time:.2f}s")
    print(f"✅ Embedding service successfully connected to Azure OpenAI")
    
    # Get deployment name if available
    deployment = getattr(embedding_service, 'deployment_name', 
                os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "unknown"))
    print(f"   Deployment: {deployment}")
    
    # Test single query embedding
    test_queries = [
        "What is Azure DevOps?",
        "How to create a pipeline in Azure DevOps?",
        "Troubleshooting build failures in Azure Pipelines",
        "Azure DevOps best practices for large teams"
    ]
    
    print("\nTesting single query embeddings:")
    for query in test_queries:
        start_time = time.time()
        embedding = embedding_service.embed_query(query)
        query_time = time.time() - start_time
        
        print(f"Query: '{query}'")
        print(f"  ↳ Embedding dimension: {len(embedding)}")
        print(f"  ↳ Generation time: {query_time:.2f}s")
        print(f"  ↳ First 5 values: {embedding[:5]}")
        print()
    
    # Test batch document embeddings
    print("\nTesting batch document embeddings:")
    start_time = time.time()
    embeddings = embedding_service.embed_documents(test_queries)
    batch_time = time.time() - start_time
    
    print(f"Batch size: {len(test_queries)}")
    print(f"  ↳ Total batch time: {batch_time:.2f}s")
    print(f"  ↳ Average per document: {batch_time/len(test_queries):.2f}s")
    print(f"  ↳ First embedding dimension: {len(embeddings[0])}")
    
    # Calculate cosine similarity between the first two embeddings
    def cosine_similarity(v1, v2):
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude1 = sum(a * a for a in v1) ** 0.5
        magnitude2 = sum(b * b for b in v2) ** 0.5
        return dot_product / (magnitude1 * magnitude2)
    
    # Compare embeddings of the first two queries
    similarity = cosine_similarity(embeddings[0], embeddings[1])
    print(f"\nSimilarity between first two queries: {similarity:.4f}")
    print("  ↳ Lower value indicates more different concepts")
    print("  ↳ Higher value indicates more similar concepts")
    
    print("\n✅ Embedding service test completed successfully with real Azure OpenAI")
    return True

if __name__ == "__main__":
    print("\n=== Testing Real Azure OpenAI Embedding Service ===\n")
    success = test_real_embedding_service()
    if not success:
        print("\n⚠️ Test completed but used mock data instead of real embeddings")
        print("Please check your Azure OpenAI credentials and connectivity")
    print("\n=== Test Completed ===") 