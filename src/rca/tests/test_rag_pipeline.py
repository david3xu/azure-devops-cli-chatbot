"""
Complete RAG pipeline test with vector search and GPT generation.
"""
import os
import time
from dotenv import load_dotenv
import requests
import json

def test_rag_pipeline():
    """Test the complete RAG pipeline."""
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
    query = "What is Azure DevOps and what are its main features?"
    
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
    start_time = time.time()
    embedding_response = requests.post(
        embedding_url,
        headers=embedding_headers,
        json=embedding_body
    )
    embedding_time = time.time() - start_time
    
    if embedding_response.status_code != 200:
        print(f"Error getting embedding: {embedding_response.status_code}")
        print(embedding_response.text)
        return
    
    embedding_result = embedding_response.json()
    query_vector = embedding_result["data"][0]["embedding"]
    print(f"Got embedding with {len(query_vector)} dimensions in {embedding_time:.2f} seconds")
    
    # Search request with vector
    search_url = f"{search_endpoint}/indexes/{search_index}/docs/search?api-version={api_version}"
    
    search_body = {
        "vectorQueries": [
            {
                "kind": "vector",
                "vector": query_vector,
                "fields": "embedding",
                "k": 5
            }
        ],
        "select": "id,content,category,sourcepage,sourcefile",
        "top": 5
    }
    
    print(f"\nSending vector search request...")
    start_time = time.time()
    search_response = requests.post(
        search_url,
        headers=headers,
        json=search_body
    )
    search_time = time.time() - start_time
    
    if search_response.status_code != 200:
        print(f"Error searching: {search_response.status_code}")
        print(search_response.text)
        return
    
    search_results = search_response.json()
    documents = search_results.get("value", [])
    
    print(f"\nFound {len(documents)} documents in {search_time:.2f} seconds:")
    for i, doc in enumerate(documents):
        print(f"{i+1}. {doc.get('id', 'Unknown')}")
        print(f"   Score: {doc.get('@search.score', 0)}")
        source_page = doc.get('sourcepage', 'No source')
        print(f"   Source: {source_page}")
        content = doc.get('content', 'No content')[:150] + "..."
        print(f"   Content: {content}\n")
    
    # Now generate response with GPT
    system_message = """You are an Azure DevOps expert assistant. Your task is to provide helpful, accurate,
and concise responses based on the context provided. If the answer is not in the context, say so politely.
Always cite your sources using [Document X] notation when referencing specific information."""
    
    # Format context
    context = ""
    for i, doc in enumerate(documents):
        content = doc.get("content", "").strip()
        source = doc.get("sourcepage", doc.get("id", "unknown"))
        context += f"[Document {i+1}] Source: {source}\n{content}\n\n"
    
    user_message = f"""Please answer the following question based on the provided context:

Question: {query}

Context:
{context}

Answer:"""
    
    # Call GPT
    chat_deployment = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "gpt-4o-mini")
    chat_url = f"{openai_endpoint}/openai/deployments/{chat_deployment}/chat/completions?api-version=2023-05-15"
    chat_headers = {
        "Content-Type": "application/json",
        "api-key": openai_key
    }
    
    chat_body = {
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 800,
        "temperature": 0.7
    }
    
    print(f"\nGenerating response with GPT ({chat_deployment})...")
    start_time = time.time()
    chat_response = requests.post(
        chat_url,
        headers=chat_headers,
        json=chat_body
    )
    generation_time = time.time() - start_time
    
    if chat_response.status_code != 200:
        print(f"Error generating response: {chat_response.status_code}")
        print(chat_response.text)
        return
    
    chat_result = chat_response.json()
    response_text = chat_result["choices"][0]["message"]["content"]
    
    print(f"\nResponse generated in {generation_time:.2f} seconds")
    print("\nGPT RESPONSE:")
    print("-" * 80)
    print(response_text)
    print("-" * 80)
    
    # Print performance summary
    total_time = embedding_time + search_time + generation_time
    print("\nPERFORMANCE SUMMARY:")
    print(f"Embedding generation: {embedding_time:.2f}s ({embedding_time/total_time*100:.1f}%)")
    print(f"Vector search:        {search_time:.2f}s ({search_time/total_time*100:.1f}%)")
    print(f"Response generation:  {generation_time:.2f}s ({generation_time/total_time*100:.1f}%)")
    print(f"Total RAG pipeline:   {total_time:.2f}s (100%)")

if __name__ == "__main__":
    test_rag_pipeline()