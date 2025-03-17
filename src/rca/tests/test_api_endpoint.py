"""
Simple FastAPI endpoint to test the agent with hybrid search.
Run with: uvicorn src.rca.tests.test_api_endpoint:app --reload
"""
import os
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import agent and connectors
from src.rca.agents.base_agent import RCAAgent
from src.rca.connectors.azure_search import AzureSearchConnector

# Load environment variables
load_dotenv(".env.azure")
print(f"Loaded environment from {os.path.abspath('.env.azure')}")

# Initialize connectors and agent
search_connector = AzureSearchConnector()
agent = RCAAgent()

# Define request and response models
class QueryRequest(BaseModel):
    query: str
    search_type: str = "hybrid"  # hybrid, vector, or semantic
    top_k: int = 3
    filter: Optional[str] = None

class SearchResult(BaseModel):
    id: str
    content: str
    score: float
    title: Optional[str] = None
    category: Optional[str] = None
    sourcepage: Optional[str] = None

class AgentResponse(BaseModel):
    query: str
    response: str
    search_results: List[Dict[str, Any]]
    search_time: float
    agent_time: float
    total_time: float
    trace_id: Optional[str] = None
    citation_indices: Optional[List[int]] = None

# Create FastAPI app
app = FastAPI(title="RAG Agent API", description="Test API for RAG Agent with Hybrid Search")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "RAG Agent API is running"}

@app.post("/query", response_model=AgentResponse)
async def process_query(request: QueryRequest):
    """Process a query using the RAG agent"""
    
    start_total = time.time()
    
    # Perform search based on search_type
    start_search = time.time()
    
    try:
        if request.search_type.lower() == "hybrid":
            search_results = search_connector.hybrid_search(
                query=request.query,
                filter=request.filter,
                top=request.top_k
            )
        elif request.search_type.lower() == "vector":
            search_results = search_connector.vector_search(
                query=request.query,
                filter=request.filter,
                top=request.top_k
            )
        elif request.search_type.lower() == "semantic":
            search_results = search_connector.semantic_search(
                query=request.query,
                filter=request.filter,
                top=request.top_k
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid search type: {request.search_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
    
    search_time = time.time() - start_search
    
    # Generate agent response using full agent processing
    start_agent = time.time()
    
    try:
        # Instead of just calling generate_response, use the full agent processing
        agent_result = agent.process(request.query)
        response = agent_result.get("response", "")
        trace_id = agent_result.get("trace_id", "")
        citation_indices = agent_result.get("citation_indices", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    
    agent_time = time.time() - start_agent
    total_time = time.time() - start_total
    
    # Return response
    return AgentResponse(
        query=request.query,
        response=response,
        search_results=search_results,
        search_time=search_time,
        agent_time=agent_time,
        total_time=total_time,
        trace_id=trace_id,
        citation_indices=citation_indices
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.rca.tests.test_api_endpoint:app", host="0.0.0.0", port=8000, reload=True) 