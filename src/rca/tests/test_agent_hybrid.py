"""
Test script to verify if the agent works with hybrid search.
This test combines vector search and semantic search to retrieve context for the agent.
"""
import os
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import agent and connectors
from src.rca.agents.base_agent import RCAAgent
from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.connectors.embeddings import AzureAdaEmbeddingService

def test_agent_with_hybrid_search():
    """Test the agent with hybrid search functionality."""
    # Load Azure environment variables
    load_dotenv(".env.azure")
    print(f"Loaded environment from {os.path.abspath('.env.azure')}")
    
    # Initialize connectors
    search_connector = AzureSearchConnector()
    embedding_service = AzureAdaEmbeddingService()
    
    # Initialize the agent
    agent = RCAAgent()
    
    # Test queries
    test_queries = [
        "What is Azure DevOps?",
        "How to create a pipeline in Azure DevOps?",
        "Compare Azure DevOps with GitHub Actions",
        "Best practices for CI/CD in Azure DevOps"
    ]
    
    for query in test_queries:
        print(f"\n\n{'='*80}")
        print(f"TESTING AGENT WITH QUERY: '{query}'")
        print(f"{'='*80}\n")
        
        # Time the hybrid search
        start_time = time.time()
        search_results = search_connector.hybrid_search(
            query=query,
            filter=None,
            top_k=3
        )
        search_time = time.time() - start_time
        print(f"Hybrid search completed in {search_time:.2f} seconds")
        
        # Display search results
        print(f"\nFound {len(search_results)} results:")
        for i, result in enumerate(search_results):
            print(f"{i+1}. {result.get('id', 'Unknown')} - Score: {result.get('score', 0)}")
            print(f"   Title: {result.get('title', 'No title')}")
            print(f"   Category: {result.get('category', 'No category')}")
            print(f"   Content: {result.get('content', '')[:150]}...\n")
        
        # Use the agent to process the query
        try:
            print("Running agent with the query...")
            start_agent_time = time.time()
            agent_result = agent.process(query)
            agent_time = time.time() - start_agent_time
            
            print(f"Agent processing completed in {agent_time:.2f} seconds")
            
            # Display agent response
            print("\nAGENT RESPONSE:")
            print(f"{'-'*80}")
            print(agent_result.get("response", "No response generated"))
            print(f"{'-'*80}")
            
            print(f"\nCitation indices: {agent_result.get('citation_indices', [])}")
            print(f"Trace ID: {agent_result.get('trace_id', 'No trace ID')}")
            
        except Exception as e:
            print(f"Error during agent processing: {str(e)}")
        
        # Give user a chance to review before next query
        if query != test_queries[-1]:
            input("\nPress Enter to continue to next query...")

if __name__ == "__main__":
    test_agent_with_hybrid_search() 