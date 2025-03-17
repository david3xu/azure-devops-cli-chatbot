# RAG System with Azure AI Search

A Retrieval Augmented Generation (RAG) system using Azure OpenAI and Azure AI Search services. This implementation provides semantic search, vector search, and hybrid search capabilities to enhance the quality of generated AI responses.

## Quickstart

### Prerequisites
- Python 3.9+
- Azure OpenAI service with "text-embedding" deployment
- Azure Search service with "gptkbindex" index
- .env.azure file with required configuration

### Setup

1. **Configure environment variables**:
   Create a `.env.azure` file in the project root with:
   ```
   AZURE_OPENAI_API_KEY=<your-openai-api-key>
   AZURE_OPENAI_ENDPOINT=<your-openai-endpoint>
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding
   AZURE_SEARCH_ADMIN_KEY=<your-search-admin-key>
   AZURE_SEARCH_ENDPOINT=<your-search-endpoint>
   AZURE_SEARCH_INDEX=gptkbindex
   AZURE_SEARCH_API_VERSION=2023-11-01
   AZURE_OPENAI_CHATGPT_DEPLOYMENT=gpt-4o-mini
   ```

2. **Run a quick test**:
   ```bash
   python -m src.rca.tests.test_minimal_rag
   ```

3. **Test the full RAG pipeline**:
   ```bash
   python -m src.rca.tests.test_rag_pipeline
   ```

### Running Endpoints

You can run the RAG system endpoints in multiple ways:

1. **Main Application Endpoint** (includes both chatbot and RCA endpoints):
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```
   This exposes:
   - `/rca/query` - Main RCA query endpoint
   - `/rca/tracking/*` - Workflow tracking endpoints
   - `/rca/visualize/*` - Visualization endpoints
   - `/chat` - Chatbot endpoint

2. **RCA API Requests** (using main endpoint):
   ```bash
   curl -X POST http://localhost:8000/rca/query \
     -H "Content-Type: application/json" \
     -d '{"query":"What is Azure DevOps?", "user_id":"test-user"}'
   ```

3. **Command Line Interface**:
   ```bash
   # Single query mode
   python -m src.rca_cli "What is Azure DevOps?"
   
   # Interactive mode
   python -m src.rca_cli --interactive
   ```

### Available Tests

- **Vector Search Test**: `python -m src.rca.tests.test_vector_search`
- **Search Connector Test**: `python -m src.rca.tests.test_azuresearch_connector`
- **Search Methods Comparison**: `python -m src.rca.tests.test_search_methods`
- **Search with GPT**: `python -m src.rca.tests.test_search_and_gpt`
- **Agent with Hybrid Search**: `python -m src.rca.tests.test_agent_hybrid`

### Test API Endpoint

Run a simple test API endpoint:
```bash
uvicorn src.rca.tests.test_api_endpoint:app --reload --host 0.0.0.0 --port 8000
```

Test with curl:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Azure DevOps?", "search_type":"hybrid", "top_k":3}'
```

## Code Examples

### Basic Vector Search

```python
from src.rca.connectors.azure_search import AzureSearchConnector

# Initialize connector
search_connector = AzureSearchConnector()

# Perform vector search
results = search_connector.vector_search(
    query="What is Azure DevOps?",
    top=3
)

# Print results
for i, result in enumerate(results):
    print(f"{i+1}. {result.get('id')} - Score: {result.get('score')}")
    print(f"   Content: {result.get('content')[:100]}...\n")
```

### Complete RAG Pipeline

```python
from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.connectors.azure_openai import AzureOpenAIConnector, ChatMessage

# Initialize connectors
search_connector = AzureSearchConnector()
openai_connector = AzureOpenAIConnector()

# Search for relevant documents
query = "What is Azure DevOps?"
search_results = search_connector.hybrid_search(query=query, top_k=3)

# Format context from search results
context = ""
for i, doc in enumerate(search_results):
    content = doc.get("content", "").strip()
    source = doc.get("id", "unknown")
    context += f"[Document {i+1}] Source: {source}\n{content}\n\n"

# Generate response with GPT
system_message = "You are an Azure DevOps expert assistant."
user_message = f"""Please answer the following question based on the provided context:
Question: {query}
Context: {context}
Answer:"""

response = openai_connector.chat_completion(
    messages=[
        ChatMessage(role="system", content=system_message),
        ChatMessage(role="user", content=user_message)
    ]
)

answer = response["choices"][0]["message"]["content"]
print(answer)
```

## Performance Benchmarks

| Search Method | Average Time | Best For |
|---------------|--------------|----------|
| Vector Search | ~5.2s | Conceptual similarity |
| Semantic Search | ~1.1s | Direct questions (fastest) |
| Hybrid Search | ~2.9s | Comprehensive results |

## Troubleshooting

- **401 Authentication Error**: Check keys in .env.azure
- **Vector Search Field Error**: Use "embedding" field and include "kind":"vector"
- **Schema Mismatch**: Verify index schema with test_minimal_rag.py

## Documentation

For more details, see `/docs/rca/` folder:
- [Testing Report](../../docs/rca/testing_report.md)
- [Implementation Progress](../../docs/rca/implementation_progress.md)
- [Implementation Files](../../docs/rca/implementation_files.md) 