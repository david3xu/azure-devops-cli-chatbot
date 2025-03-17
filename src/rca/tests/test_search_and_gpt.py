"""
Simple test script that uses Azure Search and generates a response with GPT.
This avoids using the full agent to simplify testing.
"""
import os
import time
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import connectors
from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.connectors.azure_openai import AzureOpenAIConnector, ChatMessage
from src.rca.connectors.embeddings import AzureAdaEmbeddingService

def format_context(search_results):
    """Format search results for inclusion in the prompt."""
    formatted_context = ""
    for i, result in enumerate(search_results):
        content = result.get("content", "").strip()
        source = result.get("id", "unknown")
        formatted_context += f"[Document {i+1}] Source: {source}\n{content}\n\n"
    return formatted_context

def generate_response_with_gpt(query, context, azure_openai_connector):
    """Generate a response using GPT based on the query and context."""
    system_message = """You are an Azure DevOps expert assistant. Your task is to provide helpful, accurate,
and concise responses based on the context provided. If the answer is not in the context, say so politely.
Always cite your sources using [Document X] notation when referencing specific information."""

    # Create a prompt with the context and query
    user_message = f"""Please answer the following question based on the provided context:

Question: {query}

Context:
{context}

Answer:"""

    try:
        # Send the request to Azure OpenAI using ChatMessage objects
        response = azure_openai_connector.chat_completion(
            messages=[
                ChatMessage(role="system", content=system_message),
                ChatMessage(role="user", content=user_message)
            ]
        )
        
        # Extract the response text
        if response and "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        else:
            return "Error: Could not generate a response."
    except Exception as e:
        return f"Error generating response: {str(e)}"

def test_search_and_response():
    """Test Azure Search and GPT response generation."""
    # Load Azure environment variables
    load_dotenv(".env.azure")
    print(f"Loaded environment from {os.path.abspath('.env.azure')}")
    
    # Initialize connectors
    search_connector = AzureSearchConnector()
    azure_openai = AzureOpenAIConnector()
    azure_openai.initialize()  # Explicitly initialize the connector
    embedding_service = AzureAdaEmbeddingService()
    
    # Test queries
    test_queries = [
        "What is Azure DevOps?",
        "How to create a pipeline in Azure DevOps?",
        "Compare Azure DevOps with GitHub Actions",
        "Best practices for CI/CD in Azure DevOps"
    ]
    
    for query in test_queries:
        print(f"\n\n{'='*80}")
        print(f"TESTING QUERY: '{query}'")
        print(f"{'='*80}\n")
        
        # Test different search methods
        search_methods = ["vector", "semantic", "hybrid"]
        
        for method in search_methods:
            print(f"\n--- {method.upper()} SEARCH ---\n")
            
            # Perform search
            start_time = time.time()
            
            if method == "vector":
                search_results = search_connector.vector_search(query=query, filter=None, top=3)
            elif method == "semantic":
                search_results = search_connector.semantic_search(query=query, filter=None, top=3)
            else:  # hybrid
                search_results = search_connector.hybrid_search(query=query, filter=None, top=3)
            
            search_time = time.time() - start_time
            print(f"{method.capitalize()} search completed in {search_time:.2f} seconds")
            
            # Display search results
            print(f"\nFound {len(search_results)} results:")
            for i, result in enumerate(search_results):
                print(f"{i+1}. {result.get('id', 'Unknown')} - Score: {result.get('score', 0)}")
                title = result.get('title', 'No title')
                if title:
                    print(f"   Title: {title}")
                content_preview = result.get('content', '')[:100] + "..." if result.get('content') else 'No content'
                print(f"   Content: {content_preview}\n")
            
            # Generate response
            start_time = time.time()
            context = format_context(search_results)
            response = generate_response_with_gpt(query, context, azure_openai)
            response_time = time.time() - start_time
            
            print(f"\nResponse generated in {response_time:.2f} seconds")
            print("\nGPT RESPONSE:")
            print(f"{'-'*80}")
            print(response)
            print(f"{'-'*80}")
            
            if method != search_methods[-1]:
                input("\nPress Enter to continue to next search method...")
        
        # Move to next query
        if query != test_queries[-1]:
            input("\nPress Enter to continue to next query...")

if __name__ == "__main__":
    test_search_and_response() 