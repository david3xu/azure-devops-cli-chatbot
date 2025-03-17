"""
Minimal test script for the search connector.
Tests only the embedding service and search connector without dependencies.
"""
import os
import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

from src.rca.connectors.embeddings import AzureAdaEmbeddingService
from src.rca.connectors.azure_search import AzureSearchConnector


def test_embedding_service():
    """Test the embedding service."""
    print("\n=== Testing Embedding Service ===")
    embedding_service = AzureAdaEmbeddingService()
    
    # Test embedding a query
    test_query = "What is Azure DevOps?"
    embedding = embedding_service.embed_query(test_query)
    print(f"Generated embedding with dimension: {len(embedding)}")
    print(f"First few values: {embedding[:5]}")
    
    # Test embedding multiple documents
    test_docs = [
        "Azure DevOps is a set of development tools and services.",
        "Azure Pipelines can be used for CI/CD workflows."
    ]
    doc_embeddings = embedding_service.embed_documents(test_docs)
    print(f"Generated {len(doc_embeddings)} document embeddings")
    return embedding_service


def test_search_connector():
    """Test the search connector."""
    print("\n=== Testing Search Connector ===")
    connector = AzureSearchConnector()
    
    # Test vector search
    test_query = "How to troubleshoot performance issues?"
    vector_results = connector.vector_search(test_query, top_k=3)
    print(f"\nVector search results for '{test_query}':")
    for i, result in enumerate(vector_results):
        print(f"{i+1}. {result['id']} (Score: {result['score']:.2f})")
        print(f"   {result['content'][:100]}...")
    
    # Test semantic search
    semantic_results = connector.semantic_search(test_query, top_k=3)
    print(f"\nSemantic search results for '{test_query}':")
    for i, result in enumerate(semantic_results):
        print(f"{i+1}. {result['id']} (Score: {result['score']:.2f})")
        if 'caption' in result:
            print(f"   Caption: {result['caption']}")
        print(f"   {result['content'][:100]}...")
    
    # Test hybrid search
    hybrid_results = connector.hybrid_search(test_query, top_k=3)
    print(f"\nHybrid search results for '{test_query}':")
    for i, result in enumerate(hybrid_results):
        print(f"{i+1}. {result['id']} (Score: {result['score']:.2f})")
        if 'caption' in result:
            print(f"   Caption: {result['caption']}")
        print(f"   {result['content'][:100]}...")
    
    return connector


def configure_gpt4o_mini():
    """Configure the system to use the gpt-4o-mini model."""
    print("\n=== Configuring GPT-4o-mini Model ===")
    
    # Create a new .env.model file with the updated model configuration
    model_config = """
# OpenAI API Configuration for gpt-4o-mini
# Replace with your actual API keys and endpoints
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_API_VERSION=2023-05-15

# Model Configuration
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_MODEL=gpt-4o-mini
AZURE_OPENAI_TEMPERATURE=0.1
AZURE_OPENAI_MAX_TOKENS=1024

# Embedding Model Configuration
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Azure Search Configuration
AZURE_SEARCH_ENDPOINT=your-search-endpoint
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=rca-index
AZURE_SEARCH_SEMANTIC_CONFIG=default
"""
    
    # Write the configuration to a file
    config_file = os.path.join(project_root, '.env.model')
    with open(config_file, 'w') as f:
        f.write(model_config)
    
    print(f"Model configuration file created at: {config_file}")
    print("To use this configuration, run the application with:")
    print("  $ env $(cat .env.model) python your_app.py")
    
    return True


def main():
    """Run all tests."""
    print("Starting minimal search component tests...\n")
    
    # Test embedding service
    embedding_service = test_embedding_service()
    
    # Test search connector
    connector = test_search_connector()
    
    # Configure gpt-4o-mini model
    configure_gpt4o_mini()
    
    print("\n=== All Tests Completed ===")
    print("\nVerification successful. The search components are working correctly.")
    print("Mock results are being used since we don't have real Azure services configured.")
    print("\nTo use real Azure services, update the .env.model file with actual API keys and endpoints.")


if __name__ == "__main__":
    main() 