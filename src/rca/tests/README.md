# RAG System Test Suite

This directory contains a comprehensive test suite for the Azure RAG system implementation. These tests verify all components of the system, from individual connectors to the full end-to-end pipeline.

## Available Tests

### Basic Vector Search Test
Tests vector search with the Azure Search connector using the correct 'kind' parameter:

```bash
python -m src.rca.tests.test_vector_search
```

### Comprehensive Azure Search Connector Test
Tests all search methods (vector, semantic, hybrid) in the Azure Search connector:

```bash
python -m src.rca.tests.test_azuresearch_connector
```

### Search Methods Comparison
Compares all search methods for performance and result quality:

```bash
python -m src.rca.tests.test_search_methods
```

### Complete RAG Pipeline Test
Tests the end-to-end RAG pipeline, including embedding generation, search, and response generation:

```bash
python -m src.rca.tests.test_rag_pipeline
```

### Direct Search and GPT Integration
Tests direct integration between Azure Search and Azure OpenAI:

```bash
python -m src.rca.tests.test_search_and_gpt
```

### Minimal RAG Implementation
Simple test for debugging and verifying basic connectivity:

```bash
python -m src.rca.tests.test_minimal_rag
```

### Agent with Hybrid Search
Tests the RCAAgent with hybrid search (requires fixing Pydantic issues):

```bash
python -m src.rca.tests.test_agent_hybrid
```

### FastAPI Endpoint
Run a FastAPI endpoint for testing via HTTP:

```bash
uvicorn src.rca.tests.test_api_endpoint:app --reload --host 0.0.0.0 --port 8000
```

Test with curl:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Azure DevOps?", "search_type":"hybrid", "top_k":3}'
```

## Test Results

The test results demonstrate that:

1. **Vector Search**: Successfully retrieves documents using embeddings (~5.2s)
   - Required fixing the field name to "embedding"
   - Added "kind":"vector" parameter

2. **Semantic Search**: Fast and accurate for direct questions (~1.1s)
   - Includes extractive captions and highlights
   - Best for natural language queries

3. **Hybrid Search**: Most comprehensive results combining both approaches (~2.9s)
   - Provides highest overall relevance
   - Combines strengths of vector and semantic search

4. **RAG Pipeline**: End-to-end pipeline functioning as expected
   - Total processing time: ~7.2s (Embedding: 20%, Search: 36%, Generation: 44%)
   - Generated responses correctly utilize the context

## Common Issues and Fixes

1. **Pydantic WorkflowTracker Issue**:
   - Error: "Unable to generate pydantic-core schema for WorkflowTracker"
   - Fix: Add `arbitrary_types_allowed=True` in model config

2. **Vector Search Field Error**:
   - Error: "Could not find a property named 'contentVector'"
   - Fix: Use "embedding" field name instead

3. **Vector Query Parameter Error**:
   - Error: "The vector query's 'kind' parameter is not set"
   - Fix: Include "kind":"vector" in vectorQueries

## Next Steps

We've completed the Week 1 implementation focused on Azure Search integration and are ready to move on to Week 2 tasks:

1. Implement Cosmos DB for conversation storage
2. Create interface definitions for search and embedding providers
3. Fix agent implementation to properly work with search results

For more detailed information, see the main documentation in the `/docs/rca/` folder. 