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

2. **Recording Workflow Visualization for Demos**:
   ```bash
   # 1. Start the server
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   
   # 2. Send a query to generate a trace
   curl -X POST http://localhost:8000/rca/query \
     -H "Content-Type: application/json" \
     -d '{"query":"What is Azure DevOps?", "user_id":"demo-user"}'
   
   # 3. View all traces to find the trace ID
   curl -X GET http://localhost:8000/rca/tracking/traces | grep -A2 -B2 "Azure DevOps"
   
   # 4. Open the visualization in a browser
   # http://localhost:8000/rca/visualize/traces
   # For a specific trace:
   # http://localhost:8000/rca/visualize/trace/YOUR_TRACE_ID
   
   # 5. Record demo using screen recording software
   # For Linux: Use SimpleScreenRecorder or OBS Studio
   # For Windows: Use OBS Studio or built-in Win+G recorder
   # For macOS: Use QuickTime Player or OBS Studio
   
   # 6. For non-interactive demos, prepare multiple traces in advance:
   curl -X POST http://localhost:8000/rca/query \
     -H "Content-Type: application/json" \
     -d '{"query":"How do I create a pipeline?", "user_id":"demo-user"}'
   
   curl -X POST http://localhost:8000/rca/query \
     -H "Content-Type: application/json" \
     -d '{"query":"What are best practices for DevOps?", "user_id":"demo-user"}'
   ```
   
   This visualization clearly shows the complete workflow of the agent:
   - Each workflow step (vector search, document ranking, response generation)
   - Inputs and outputs at each step
   - Processing time for each operation
   - Documents retrieved and their scores
   - The final generated response
   
   The HTML-based visualization is ideal for presentations and demos, showing exactly how the RAG pipeline works end-to-end.

3. **Test API Endpoint** (for testing RAG functionalities):
   ```bash
   uvicorn src.rca.tests.test_api_endpoint:app --reload --host 0.0.0.0 --port 8000
   ```

   If port 8000 is already in use, you can kill existing processes and restart:
   ```bash
   # Find processes using port 8000
   lsof -i :8000
   
   # Kill the processes (replace PIDs with actual values)
   kill -9 <PID1> <PID2>
   
   # Start the server
   uvicorn src.rca.tests.test_api_endpoint:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Testing All API Endpoints Step by Step**

   The system consists of several API endpoint modules:
   - `endpoints.py` - Main RCA query endpoints
   - `tracking_endpoints.py` - Workflow tracking endpoints
   - `visualization.py` - HTML visualization endpoints

   To test all these endpoints, follow these steps:

   **Step 1: Start the main application**
   ```bash
   # Make sure no other process is using port 8000
   lsof -i :8000
   kill -9 <PID> # if needed
   
   # Start the server
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

   **Step 2: Test the main RCA query endpoint (endpoints.py)**
   ```bash
   # Submit a query
   curl -X POST http://localhost:8000/rca/query \
     -H "Content-Type: application/json" \
     -d '{"query":"What is Azure DevOps?", "user_id":"test-user"}'
   
   # Save the query_id from the response for the next steps
   # Example response will include: "query_id": "abc123"
   ```

   **Step 3: Test the feedback endpoint (endpoints.py)**
   ```bash
   # Replace QUERY_ID with an actual ID from the previous step
   curl -X POST http://localhost:8000/rca/feedback \
     -H "Content-Type: application/json" \
     -d '{"query_id":"QUERY_ID", "rating":5, "comments":"Great response!"}'
   ```

   **Step 4: Test the workflow tracking endpoints (tracking_endpoints.py)**
   ```bash
   # List all recent traces
   curl -X GET http://localhost:8000/rca/tracking/traces
   
   # View a specific trace (replace TRACE_ID with an actual ID from the list)
   curl -X GET http://localhost:8000/rca/tracking/traces/TRACE_ID
   ```

   **Step 5: Test the visualization endpoints (visualization.py)**
   These are best viewed in a browser:
   ```bash
   # Open these URLs in a browser
   http://localhost:8000/rca/visualize/traces
   http://localhost:8000/rca/visualize/trace/TRACE_ID  # Replace with actual trace ID
   ```

   **Step 6: View API documentation**
   FastAPI automatically generates interactive documentation:
   ```bash
   # Open in browser
   http://localhost:8000/docs
   ```

   **Troubleshooting**: 
   - If you encounter connection issues, make sure no other process is using port 8000
   - Check the server logs for error messages
   - Verify that the endpoints are correctly registered in src.main:app

5. **Test Specific Search Methods with the Test API Endpoint**:
   ```bash
   # Start the test API endpoint
   uvicorn src.rca.tests.test_api_endpoint:app --reload --host 0.0.0.0 --port 8000
   
   # Test hybrid search
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query":"What is Azure DevOps?", "search_type":"hybrid", "top_k":3}'
   
   # Test vector search
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query":"How to create a pipeline in Azure DevOps?", "search_type":"vector", "top_k":3}'
   
   # Test semantic search
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query":"Best practices for Azure DevOps?", "search_type":"semantic", "top_k":3}'
   ```

   **Note**: The parameter for number of results is consistently named `top_k` across all search methods in the API. The underlying `AzureSearchConnector` class has been updated to use `top_k` instead of `top` in the `vector_search` method for consistency.

6. **Command Line Interface**:
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
- **Comprehensive Test**: `python -m src.rca.tests.test_all_functionality`

## Code Examples

### Basic Vector Search

```python
from src.rca.connectors.azure_search import AzureSearchConnector

# Initialize connector
search_connector = AzureSearchConnector()

# Perform vector search
results = search_connector.vector_search(
    query="What is Azure DevOps?",
    top_k=3
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
| Vector Search | ~3.0s | Conceptual similarity |
| Semantic Search | ~1.1s | Direct questions (fastest) |
| Hybrid Search | ~2.0s | Comprehensive results |

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what process is using port 8000
   lsof -i :8000
   
   # Kill the process
   kill -9 <PID>
   ```

2. **Parameter Mismatches**
   - The search methods in `AzureSearchConnector` now consistently use `top_k` as the parameter name for specifying the number of results to return.
   - If you encounter errors about unexpected keyword arguments, check that you're using the correct parameter names.

3. **URL Formatting Issues**
   - If you encounter errors about malformed URLs, check that the URLs in your configuration don't have extra quotes or characters.
   - The embedding service URL should be properly formatted without extra quotes.

4. **API Endpoint Not Found**
   - Verify that you're using the correct endpoint path.
   - For the test API, use `/query` instead of `/rca/query`.
   - For the main application, use `/rca/query` as the endpoint path.

5. **Server Not Starting**
   - Check for error messages in the console output.
   - Ensure all required environment variables are set in `.env.azure`.
   - Verify that all dependencies are installed.

## Documentation

For more details, see `/docs/rca/` folder:
- [Testing Report](../../docs/rca/testing_report.md)
- [Implementation Progress](../../docs/rca/implementation_progress.md)
- [Implementation Files](../../docs/rca/implementation_files.md)

## GitHub Workflow

Follow these steps to update the codebase:

1. **Clone and branch**:
   ```bash
   # If first time: Clone the repository
   git clone https://github.com/user/azure-devops-cli-chatbot.git
   cd azure-devops-cli-chatbot
   
   # Create a feature branch
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test**:
   ```bash
   # Make your code changes
   # Run tests to verify functionality
   python -m src.rca.tests.test_minimal_rag
   ```

3. **Commit and push changes**:
   ```bash
   # Check what files have changed
   git status
   
   # Add specific files
   git add src/rca/connectors/azure_search.py
   
   # Or add all changed files
   git add .
   
   # Commit with descriptive message
   git commit -m "Implement semantic search in Azure Search connector"
   
   # Push to your feature branch
   git push origin feature/your-feature-name
   ```

4. **Create pull request**:
   - Go to GitHub repository
   - Click "Compare & pull request" for your branch
   - Fill out PR template with details about your changes
   - Submit the PR for review

The team typically reviews PRs within 2 business days. Make sure all tests pass in the CI/CD pipeline before requesting review. 