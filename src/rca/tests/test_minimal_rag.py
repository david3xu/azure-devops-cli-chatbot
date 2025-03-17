"""
Minimal test to verify Azure Search and GPT functionality.
"""
import os
import time
from dotenv import load_dotenv
import requests
import json

def test_search():
    """Test Azure Search service."""
    # Load environment variables
    load_dotenv(".env.azure")
    
    # Configure Azure Search
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
    search_index = os.getenv("AZURE_SEARCH_INDEX")
    api_version = os.getenv("AZURE_SEARCH_API_VERSION", "2023-11-01")
    
    print(f"Search endpoint: {search_endpoint}")
    print(f"Search index: {search_index}")
    print(f"Key available: {'Yes' if search_key else 'No'}")
    
    # Prepare search request
    headers = {
        "Content-Type": "application/json",
        "api-key": search_key
    }
    
    # Vector search query
    query = "What is Azure DevOps?"
    
    # Get embedding from Azure OpenAI
    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai_key = os.getenv("AZURE_OPENAI_API_KEY")
    embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding")
    
    embedding_url = f"{openai_endpoint}/openai/deployments/{embedding_deployment}/embeddings?api-version=2023-05-15"
    embedding_headers = {
        "Content-Type": "application/json",
        "api-key": openai_key
    }
    
    embedding_body = {
        "input": query,
        "model": "text-embedding-ada-002"
    }
    
    print(f"\nGetting embedding for query: '{query}'")
    embedding_response = requests.post(
        embedding_url,
        headers=embedding_headers,
        json=embedding_body
    )
    
    if embedding_response.status_code != 200:
        print(f"Error getting embedding: {embedding_response.status_code}")
        print(embedding_response.text)
        return
    
    embedding_result = embedding_response.json()
    query_vector = embedding_result["data"][0]["embedding"]
    print(f"Got embedding with {len(query_vector)} dimensions")
    
    # Search request with vector
    search_url = f"{search_endpoint}/indexes/{search_index}/docs/search?api-version={api_version}"
    
    search_body = {
        "vectorQueries": [
            {
                "kind": "vector",
                "vector": query_vector,
                "fields": "embedding",
                "k": 3
            }
        ],
        "select": "id,content,category,sourcepage,sourcefile",
        "top": 3
    }
    
    print(f"\nSending search request to {search_url}")
    search_response = requests.post(
        search_url,
        headers=headers,
        json=search_body
    )
    
    if search_response.status_code != 200:
        print(f"Error searching: {search_response.status_code}")
        print(search_response.text)
        return
    
    search_results = search_response.json()
    documents = search_results.get("value", [])
    
    print(f"\nFound {len(documents)} documents:")
    for i, doc in enumerate(documents):
        print(f"{i+1}. {doc.get('id', 'Unknown')}")
        print(f"   Score: {doc.get('@search.score', 0)}")
        content = doc.get('content', 'No content')[:100] + "..."
        print(f"   Content: {content}\n")
    
    # Now generate response with GPT
    system_message = "You are an Azure DevOps expert assistant. Please answer questions based on the context provided."
    
    # Format context
    context = ""
    for i, doc in enumerate(documents):
        content = doc.get("content", "").strip()
        source = doc.get("id", "unknown")
        context += f"[Document {i+1}] Source: {source}\n{content}\n\n"
    
    user_message = f"""Please answer the following question based on the provided context:

Question: {query}

Context:
{context}

Answer:"""
    
    # Call GPT
    chat_url = f"{openai_endpoint}/openai/deployments/gpt-4o-mini/chat/completions?api-version=2023-05-15"
    chat_headers = {
        "Content-Type": "application/json",
        "api-key": openai_key
    }
    
    chat_body = {
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    print(f"\nGenerating response with GPT...")
    chat_response = requests.post(
        chat_url,
        headers=chat_headers,
        json=chat_body
    )
    
    if chat_response.status_code != 200:
        print(f"Error generating response: {chat_response.status_code}")
        print(chat_response.text)
        return
    
    chat_result = chat_response.json()
    response_text = chat_result["choices"][0]["message"]["content"]
    
    print("\nGPT RESPONSE:")
    print("-" * 80)
    print(response_text)
    print("-" * 80)

if __name__ == "__main__":
    test_search() 