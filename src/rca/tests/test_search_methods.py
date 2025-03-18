"""
Comprehensive test for all search methods.
Compares vector, semantic, and hybrid search results.
"""
import os
import sys
import time
import logging
import json
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '.env.azure')
load_dotenv(env_file)
print(f"Loading environment from {env_file}")

# Import our connectors
from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.connectors.embeddings import AzureAdaEmbeddingService

def test_search_methods():
    """Test all search methods and compare results."""
    # Load Azure environment variables
    load_dotenv(".env.azure")
    print(f"Loaded environment from {os.path.abspath('.env.azure')}")
    
    # Initialize connectors
    search_connector = AzureSearchConnector()
    embedding_service = AzureAdaEmbeddingService()
    
    # Test queries
    test_queries = [
        "What is Azure DevOps?",
        "How to create a pipeline in Azure DevOps?",
        "Troubleshooting build failures in Azure Pipelines",
        "Azure DevOps best practices for large teams"
    ]
    
    # Results summary
    results_summary = {
        "vector": {"total_time": 0, "avg_time": 0, "queries": {}},
        "semantic": {"total_time": 0, "avg_time": 0, "queries": {}},
        "hybrid": {"total_time": 0, "avg_time": 0, "queries": {}}
    }
    
    for query in test_queries:
        print(f"\n\n{'='*80}")
        print(f"TESTING QUERY: '{query}'")
        print(f"{'='*80}\n")
        
        query_results = {}
        
        # Test vector search
        print("\n--- VECTOR SEARCH ---\n")
        start_time = time.time()
        vector_results = search_connector.vector_search(query=query, top_k=5)
        vector_time = time.time() - start_time
        
        print(f"Vector search completed in {vector_time:.2f} seconds")
        print(f"Found {len(vector_results)} results:")
        for i, result in enumerate(vector_results):
            if i < 3:  # Show only top 3 for brevity
                print(f"{i+1}. {result.get('id', 'Unknown')} - Score: {result.get('score', 0)}")
                content_preview = result.get('content', '')[:100] + "..." if result.get('content') else 'No content'
                print(f"   Content: {content_preview}\n")
        
        # Store results for comparison
        query_results["vector"] = {
            "time": vector_time,
            "results": vector_results,
            "result_ids": [r.get("id") for r in vector_results]
        }
        results_summary["vector"]["total_time"] += vector_time
        results_summary["vector"]["queries"][query] = {
            "time": vector_time,
            "result_count": len(vector_results)
        }
        
        # Test semantic search
        print("\n--- SEMANTIC SEARCH ---\n")
        start_time = time.time()
        semantic_results = search_connector.semantic_search(query=query, top_k=5)
        semantic_time = time.time() - start_time
        
        print(f"Semantic search completed in {semantic_time:.2f} seconds")
        print(f"Found {len(semantic_results)} results:")
        for i, result in enumerate(semantic_results):
            if i < 3:  # Show only top 3 for brevity
                print(f"{i+1}. {result.get('id', 'Unknown')} - Score: {result.get('score', 0)}")
                caption = result.get('caption', 'No caption')
                print(f"   Caption: {caption}")
                content_preview = result.get('content', '')[:100] + "..." if result.get('content') else 'No content'
                print(f"   Content: {content_preview}\n")
        
        # Store results for comparison
        query_results["semantic"] = {
            "time": semantic_time,
            "results": semantic_results,
            "result_ids": [r.get("id") for r in semantic_results]
        }
        results_summary["semantic"]["total_time"] += semantic_time
        results_summary["semantic"]["queries"][query] = {
            "time": semantic_time,
            "result_count": len(semantic_results)
        }
        
        # Test hybrid search
        print("\n--- HYBRID SEARCH ---\n")
        start_time = time.time()
        hybrid_results = search_connector.hybrid_search(query=query, top_k=5)
        hybrid_time = time.time() - start_time
        
        print(f"Hybrid search completed in {hybrid_time:.2f} seconds")
        print(f"Found {len(hybrid_results)} results:")
        for i, result in enumerate(hybrid_results):
            if i < 3:  # Show only top 3 for brevity
                print(f"{i+1}. {result.get('id', 'Unknown')} - Score: {result.get('score', 0)}")
                content_preview = result.get('content', '')[:100] + "..." if result.get('content') else 'No content'
                print(f"   Content: {content_preview}\n")
        
        # Store results for comparison
        query_results["hybrid"] = {
            "time": hybrid_time,
            "results": hybrid_results,
            "result_ids": [r.get("id") for r in hybrid_results]
        }
        results_summary["hybrid"]["total_time"] += hybrid_time
        results_summary["hybrid"]["queries"][query] = {
            "time": hybrid_time,
            "result_count": len(hybrid_results)
        }
        
        # Compare results
        print("\n--- RESULT COMPARISON ---\n")
        
        # Compare result overlap
        vector_ids = set(query_results["vector"]["result_ids"])
        semantic_ids = set(query_results["semantic"]["result_ids"])
        hybrid_ids = set(query_results["hybrid"]["result_ids"])
        
        vector_semantic_overlap = len(vector_ids.intersection(semantic_ids))
        vector_hybrid_overlap = len(vector_ids.intersection(hybrid_ids))
        semantic_hybrid_overlap = len(semantic_ids.intersection(hybrid_ids))
        
        print(f"Vector-Semantic overlap: {vector_semantic_overlap} documents")
        print(f"Vector-Hybrid overlap: {vector_hybrid_overlap} documents")
        print(f"Semantic-Hybrid overlap: {semantic_hybrid_overlap} documents")
        
        # Compare performance
        print("\n--- PERFORMANCE COMPARISON ---\n")
        print(f"Vector search:  {vector_time:.2f}s")
        print(f"Semantic search: {semantic_time:.2f}s")
        print(f"Hybrid search:  {hybrid_time:.2f}s")
        
        # Continue to next query
        if query != test_queries[-1]:
            input("\nPress Enter to continue to next query...")
    
    # Calculate averages
    query_count = len(test_queries)
    for method in results_summary:
        results_summary[method]["avg_time"] = results_summary[method]["total_time"] / query_count
    
    # Print overall summary
    print(f"\n\n{'='*80}")
    print(f"OVERALL SEARCH PERFORMANCE SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"Vector search:  {results_summary['vector']['avg_time']:.2f}s average")
    print(f"Semantic search: {results_summary['semantic']['avg_time']:.2f}s average")
    print(f"Hybrid search:  {results_summary['hybrid']['avg_time']:.2f}s average")
    
    print("\nSearch method comparison complete!")

if __name__ == "__main__":
    test_search_methods() 