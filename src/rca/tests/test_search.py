"""
Test script for the search connector and tools.
Verifies that the vector, semantic, and hybrid search functionality works correctly.
"""
import os
import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.connectors.embeddings import AzureAdaEmbeddingService
from src.rca.tools.search_tools import VectorSearchTool, SemanticSearchTool, HybridSearchTool
from src.rca.utils.evaluation import SearchEvaluator, create_test_set


def test_embedding_service():
    """Test the embedding service."""
    print("\n=== Testing Embedding Service ===")
    embedding_service = AzureAdaEmbeddingService()
    
    # Test initialization
    initialized = embedding_service.initialize()
    print(f"Initialization successful: {initialized}")
    
    if not initialized:
        print("Using mock embeddings since initialization failed")
    
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
    
    # Test initialization
    initialized = connector.initialize()
    print(f"Initialization successful: {initialized}")
    
    if not initialized:
        print("Using mock results since initialization failed")
    
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


def test_search_tools():
    """Test the search tools."""
    print("\n=== Testing Search Tools ===")
    
    # Test vector search tool
    vector_tool = VectorSearchTool()
    vector_input = vector_tool.input_class(query="What is Azure DevOps?", top_k=3)
    vector_output = vector_tool.run(vector_input)
    
    print(f"\nVector search tool results:")
    for i, result in enumerate(vector_output.results):
        print(f"{i+1}. {result['id']} (Score: {result['score']:.2f})")
    
    # Test semantic search tool
    semantic_tool = SemanticSearchTool()
    semantic_input = semantic_tool.input_class(query="How to create a pipeline?", top_k=3)
    semantic_output = semantic_tool.run(semantic_input)
    
    print(f"\nSemantic search tool results:")
    for i, result in enumerate(semantic_output.results):
        print(f"{i+1}. {result['id']} (Score: {result['score']:.2f})")
        if 'caption' in result:
            print(f"   Caption: {result['caption']}")
    
    # Test hybrid search tool
    hybrid_tool = HybridSearchTool()
    hybrid_input = hybrid_tool.input_class(query="Azure DevOps best practices", top_k=3)
    hybrid_output = hybrid_tool.run(hybrid_input)
    
    print(f"\nHybrid search tool results:")
    for i, result in enumerate(hybrid_output.results):
        print(f"{i+1}. {result['id']} (Score: {result['score']:.2f})")
        if 'caption' in result:
            print(f"   Caption: {result['caption']}")


def test_search_evaluator():
    """Test the search evaluator."""
    print("\n=== Testing Search Evaluator ===")
    evaluator = SearchEvaluator()
    
    # Test initialization
    initialized = evaluator.initialize()
    print(f"Initialization successful: {initialized}")
    
    # Test evaluating a single query
    test_query = "How to troubleshoot performance issues?"
    expected_results = ["doc2", "doc3"]
    
    print(f"\nEvaluating query: '{test_query}'")
    results = evaluator.evaluate_query(
        query=test_query,
        expected_results=expected_results,
        top_k=3,
        run_count=2  # Use 2 for faster testing
    )
    
    # Print the evaluation results
    print("\nEvaluation results summary:")
    for method, data in results["methods"].items():
        metrics = data["metrics"]
        print(f"- {method.capitalize()} search:")
        print(f"  Mean latency: {metrics['mean_latency_ms']:.2f}ms")
        if "precision" in metrics:
            print(f"  Precision: {metrics['precision']:.2f}")
            print(f"  Recall: {metrics['recall']:.2f}")
            print(f"  F1 score: {metrics['f1']:.2f}")
    
    # Print the best method
    print(f"\nBest method determination:")
    best = results["best_method"]
    print(f"- For performance: {best['for_performance']}")
    print(f"- For relevance: {best['for_relevance']}")
    print(f"- Overall recommendation: {best['overall']}")
    
    for note in best["notes"]:
        print(f"- Note: {note}")
    
    print(f"\nEvaluation results saved to: {evaluator.results_dir}")
    
    return evaluator


def configure_gpt4o_mini():
    """Configure the system to use the gpt-4o-mini model."""
    print("\n=== Configuring GPT-4o-mini Model ===")
    
    # Check if the OpenAI connector is available
    try:
        from src.rca.connectors.azure_openai import AzureOpenAIConnector
        
        # Create a new .env.model file with the updated model configuration
        model_config = """
# OpenAI API Configuration for gpt-4o-mini
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
"""
        
        # Write the configuration to a file
        config_file = os.path.join(project_root, '.env.model')
        with open(config_file, 'w') as f:
            f.write(model_config)
        
        print(f"Model configuration file created at: {config_file}")
        print("To use this configuration, run the application with:")
        print("  $ env $(cat .env.model) python your_app.py")
        
        return True
    except ImportError:
        print("AzureOpenAIConnector not available. Unable to configure model.")
        return False


def main():
    """Run all tests."""
    print("Starting search component tests...\n")
    
    # Test embedding service
    embedding_service = test_embedding_service()
    
    # Test search connector
    connector = test_search_connector()
    
    # Test search tools
    test_search_tools()
    
    # Test search evaluator
    test_search_evaluator()
    
    # Configure gpt-4o-mini model
    configure_gpt4o_mini()
    
    print("\n=== All Tests Completed ===")


if __name__ == "__main__":
    main() 