"""
Comprehensive test for the updated AzureSearchConnector.
Tests vector, semantic, and hybrid search with real Azure Search.
"""
import os
import time
from dotenv import load_dotenv

from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.connectors.embeddings import AzureAdaEmbeddingService

def test_search_connector():
    """Test the AzureSearchConnector with real Azure Search."""
    # Load Azure environment variables
    load_dotenv(".env.azure")
    
    # Initialize connectors
    search_connector = AzureSearchConnector()
    embedding_service = AzureAdaEmbeddingService()
    
    # Print Azure Search information
    print(f"Azure Search Connector Settings:")
    print(f"  Endpoint: {search_connector.endpoint}")
    print(f"  Index: {search_connector.index_name}")
    print(f"  API Version: {search_connector.api_version}")
    print(f"  Key available: {'Yes' if search_connector.key else 'No'}")
    
    # Test queries
    test_queries = [
        "What is Azure DevOps?",
        "How to set up CI/CD pipelines in Azure DevOps?",
        "What are the best practices for Azure DevOps repos?",
        "How to integrate Azure DevOps with GitHub?"
    ]
    
    for query in test_queries:
        print(f"\n\n{'='*80}")
        print(f"TESTING QUERY: '{query}'")
        print(f"{'='*80}\n")
        
        # Test vector search
        print("\n--- VECTOR SEARCH ---\n")
        start_time = time.time()
        vector_results = search_connector.vector_search(query=query, top_k=3)
        vector_time = time.time() - start_time
        
        print(f"Vector search completed in {vector_time:.2f} seconds")
        print(f"Found {len(vector_results)} results:")
        for i, result in enumerate(vector_results):
            print(f"{i+1}. {result.get('id', 'Unknown')}")
            print(f"   Score: {result.get('score', 0)}")
            source = result.get('sourcepage', 'No source')
            print(f"   Source: {source}")
            content = result.get('content', 'No content')[:150] + "..."
            print(f"   Content: {content}\n")
        
        # Test semantic search
        print("\n--- SEMANTIC SEARCH ---\n")
        start_time = time.time()
        semantic_results = search_connector.semantic_search(query=query, top_k=3)
        semantic_time = time.time() - start_time
        
        print(f"Semantic search completed in {semantic_time:.2f} seconds")
        print(f"Found {len(semantic_results)} results:")
        for i, result in enumerate(semantic_results):
            print(f"{i+1}. {result.get('id', 'Unknown')}")
            print(f"   Score: {result.get('score', 0)}")
            source = result.get('sourcepage', 'No source')
            print(f"   Source: {source}")
            caption = result.get('caption', 'No caption')
            print(f"   Caption: {caption}")
            content = result.get('content', 'No content')[:150] + "..."
            print(f"   Content: {content}\n")
        
        # Test hybrid search
        print("\n--- HYBRID SEARCH ---\n")
        start_time = time.time()
        hybrid_results = search_connector.hybrid_search(query=query, top_k=3)
        hybrid_time = time.time() - start_time
        
        print(f"Hybrid search completed in {hybrid_time:.2f} seconds")
        print(f"Found {len(hybrid_results)} results:")
        for i, result in enumerate(hybrid_results):
            print(f"{i+1}. {result.get('id', 'Unknown')}")
            print(f"   Score: {result.get('score', 0)}")
            source = result.get('sourcepage', 'No source')
            print(f"   Source: {source}")
            content = result.get('content', 'No content')[:150] + "..."
            print(f"   Content: {content}\n")
        
        # Compare performance
        print("\n--- PERFORMANCE COMPARISON ---\n")
        print(f"Vector search:  {vector_time:.2f}s")
        print(f"Semantic search: {semantic_time:.2f}s")
        print(f"Hybrid search:  {hybrid_time:.2f}s")
        
        # Continue to next query
        if query != test_queries[-1]:
            input("\nPress Enter to continue to next query...")

if __name__ == "__main__":
    test_search_connector() 