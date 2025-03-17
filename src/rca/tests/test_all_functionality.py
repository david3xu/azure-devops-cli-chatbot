"""
Test all main functionality of the RAG system.
This test script runs a comprehensive check of the entire RAG pipeline.
"""
import os
import sys
import time
from pathlib import Path
import requests

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

from src.rca.connectors.embeddings import AzureAdaEmbeddingService
from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.connectors.azure_openai import AzureOpenAIConnector, ChatMessage
from src.rca.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Load environment variables
env_file = os.path.join(project_root, ".env.azure")
if os.path.exists(env_file):
    print(f"Loading environment from {env_file}")
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
else:
    print("Warning: .env.azure file not found")

def test_embedding():
    """Test the embedding service."""
    print("\n=== Testing Embedding Service ===")
    embedding_service = AzureAdaEmbeddingService()
    
    # Test query embedding
    query = "What is Azure DevOps?"
    print(f"Embedding query: '{query}'")
    start_time = time.time()
    embedding = embedding_service.embed_query(query)
    embed_time = time.time() - start_time
    
    print(f"Embedding dimensions: {len(embedding)}")
    print(f"Embedding time: {embed_time:.2f}s")
    
    assert len(embedding) == 1536, f"Expected 1536 dimensions, got {len(embedding)}"
    return embedding_service

def test_search(embedding_service):
    """Test the search connector."""
    print("\n=== Testing Search Connector ===")
    search_connector = AzureSearchConnector()
    
    # Verify connection to search service
    print(f"Search service: {search_connector.service_name}")
    print(f"Search index: {search_connector.index_name}")
    
    # Get document count directly using the API
    try:
        search_url = f"{search_connector.endpoint}/indexes/{search_connector.index_name}/docs/count?api-version={search_connector.api_version}"
        # Remove any double quotes from the URL
        search_url = search_url.replace('"', '')
        headers = {
            "Content-Type": "application/json",
            "api-key": search_connector.key.replace('"', '')  # Remove any quotes from the key
        }
        response = requests.get(search_url, headers=headers)
        if response.status_code == 200:
            count = response.json()
            print(f"Document count: {count}")
        else:
            print(f"Failed to get document count: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error getting document count: {str(e)}")
    
    # Test queries
    test_queries = [
        "What is Azure DevOps?",
        "How to create a pipeline in Azure DevOps?"
    ]
    
    # Test vector search
    print("\n--- Vector Search ---")
    for query in test_queries:
        print(f"Query: '{query}'")
        start_time = time.time()
        results = search_connector.vector_search(query, top_k=3)
        search_time = time.time() - start_time
        
        print(f"  ↳ Search time: {search_time:.2f}s")
        print(f"  ↳ Results: {len(results)}")
        for i, result in enumerate(results[:2]):
            print(f"    {i+1}. {result.get('id', 'unknown')} - Score: {result.get('score', 0):.4f}")
            content = result.get('content', '')
            print(f"       {content[:100]}..." if content else "       No content")
    
    # Test semantic search
    print("\n--- Semantic Search ---")
    for query in test_queries:
        print(f"Query: '{query}'")
        start_time = time.time()
        results = search_connector.semantic_search(query, top_k=3)
        search_time = time.time() - start_time
        
        print(f"  ↳ Search time: {search_time:.2f}s")
        print(f"  ↳ Results: {len(results)}")
        for i, result in enumerate(results[:2]):
            print(f"    {i+1}. {result.get('id', 'unknown')} - Score: {result.get('score', 0):.4f}")
            caption = result.get('caption', '')
            print(f"       Caption: {caption[:100]}..." if caption else "       No caption")
    
    # Test hybrid search
    print("\n--- Hybrid Search ---")
    for query in test_queries:
        print(f"Query: '{query}'")
        start_time = time.time()
        results = search_connector.hybrid_search(query, top_k=3)
        search_time = time.time() - start_time
        
        print(f"  ↳ Search time: {search_time:.2f}s")
        print(f"  ↳ Results: {len(results)}")
        for i, result in enumerate(results[:2]):
            print(f"    {i+1}. {result.get('id', 'unknown')} - Score: {result.get('score', 0):.4f}")
            content = result.get('content', '')
            print(f"       {content[:100]}..." if content else "       No content")
            
    return search_connector

def test_openai():
    """Test the OpenAI connector."""
    print("\n=== Testing OpenAI Connector ===")
    openai_connector = AzureOpenAIConnector()
    
    print(f"Model: {openai_connector.model}")
    print(f"Deployment: {openai_connector.deployment}")
    
    # Test simple chat completion
    prompt = "What is Azure DevOps in one sentence?"
    print(f"Prompt: '{prompt}'")
    
    start_time = time.time()
    response = openai_connector.chat_completion([
        ChatMessage(role="system", content="You are a helpful assistant specialized in Azure DevOps."),
        ChatMessage(role="user", content=prompt)
    ])
    completion_time = time.time() - start_time
    
    response_text = openai_connector.get_completion_text(response)
    print(f"Response time: {completion_time:.2f}s")
    print(f"Response: '{response_text}'")
    
    return openai_connector

def test_rag_pipeline(search_connector, openai_connector):
    """Test the full RAG pipeline."""
    print("\n=== Testing Complete RAG Pipeline ===")
    
    # Query and search for context
    query = "What are the main features of Azure DevOps?"
    print(f"Query: '{query}'")
    
    # Get search results for context
    start_time = time.time()
    search_results = search_connector.hybrid_search(query, top_k=3)
    search_time = time.time() - start_time
    print(f"Search time: {search_time:.2f}s")
    
    # Format context
    context = ""
    for i, result in enumerate(search_results):
        content = result.get('content', '').strip()
        source = result.get('id', f'doc{i}')
        context += f"[Document {i+1}] Source: {source}\n{content}\n\n"
    
    # Generate response with context
    system_message = "You are an expert assistant specialized in Azure DevOps."
    user_message = f"""Please answer the following question based on the provided context:
    
Question: {query}

Context:
{context}

Answer:"""
    
    # Get chat completion
    completion_start = time.time()
    response = openai_connector.chat_completion([
        ChatMessage(role="system", content=system_message),
        ChatMessage(role="user", content=user_message)
    ])
    completion_time = time.time() - completion_start
    
    response_text = openai_connector.get_completion_text(response)
    
    total_time = time.time() - start_time
    print(f"Response time: {completion_time:.2f}s")
    print(f"Total RAG pipeline time: {total_time:.2f}s")
    print("\nRAG Response:")
    print("="*80)
    print(response_text)
    print("="*80)
    
    # Calculate timing breakdown
    search_percent = (search_time / total_time) * 100
    completion_percent = (completion_time / total_time) * 100
    overhead = total_time - search_time - completion_time
    overhead_percent = (overhead / total_time) * 100
    
    print("\nPerformance Breakdown:")
    print(f"Search:     {search_time:.2f}s ({search_percent:.1f}%)")
    print(f"Generation: {completion_time:.2f}s ({completion_percent:.1f}%)")
    print(f"Overhead:   {overhead:.2f}s ({overhead_percent:.1f}%)")
    print(f"Total:      {total_time:.2f}s (100%)")

def main():
    """Run all tests."""
    try:
        # Run embedding test
        embedding_service = test_embedding()
        
        # Run search tests
        search_connector = test_search(embedding_service)
        
        # Run OpenAI test
        openai_connector = test_openai()
        
        # Run full RAG pipeline test
        test_rag_pipeline(search_connector, openai_connector)
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Tests failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 