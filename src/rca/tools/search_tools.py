"""
Search tools for the RCA system.
Provides search tools using Azure AI Search with vector, semantic, and hybrid search.
"""
from typing import Dict, List, Optional, Any
from pydantic import Field, BaseModel

from src.rca.tools.base_tool import BaseTool
from src.rca.connectors.azure_search import AzureSearchConnector


class VectorSearchInput(BaseModel):
    """Input for VectorSearchTool."""
    
    query: str = Field(
        ...,
        description="The search query text",
    )
    top_k: int = Field(
        5,
        description="Number of results to return",
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional filters for search (e.g. {'category': 'troubleshooting'})",
    )


class VectorSearchOutput(BaseModel):
    """Output from VectorSearchTool."""
    
    results: List[Dict[str, Any]] = Field(
        ...,
        description="List of search results",
    )


class VectorSearchTool(BaseTool[VectorSearchInput, VectorSearchOutput]):
    """Tool for performing vector search."""
    
    name = "vector_search"
    description = "Search for information using vector search"
    input_model = VectorSearchInput
    output_model = VectorSearchOutput
    connector: AzureSearchConnector = None
    
    def __init__(self):
        """Initialize the vector search tool."""
        super().__init__()
        self.connector = AzureSearchConnector()
    
    def _execute(self, input_data: VectorSearchInput) -> Dict[str, Any]:
        """
        Execute vector search.
        
        Args:
            input_data: Search parameters
            
        Returns:
            Search results
        """
        # Initialize connector if not already done
        if not self.connector:
            self.connector = AzureSearchConnector()
            
        # Perform search
        results = self.connector.vector_search(
            query=input_data.query,
            top_k=input_data.top_k,
            filter=input_data.filters
        )
        
        return {"results": results}


class SemanticSearchInput(BaseModel):
    """Input for SemanticSearchTool."""
    
    query: str = Field(
        ...,
        description="The search query text",
    )
    top_k: int = Field(
        5,
        description="Number of results to return",
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional filters for search (e.g. {'category': 'troubleshooting'})",
    )


class SemanticSearchOutput(BaseModel):
    """Output from SemanticSearchTool."""
    
    results: List[Dict[str, Any]] = Field(
        ...,
        description="List of search results with semantic captions",
    )


class SemanticSearchTool(BaseTool[SemanticSearchInput, SemanticSearchOutput]):
    """Tool for performing semantic search."""
    
    name = "semantic_search"
    description = "Search for information using semantic search with extractive captions"
    input_model = SemanticSearchInput
    output_model = SemanticSearchOutput
    connector: AzureSearchConnector = None
    
    def __init__(self):
        """Initialize the semantic search tool."""
        super().__init__()
        self.connector = AzureSearchConnector()
    
    def _execute(self, input_data: SemanticSearchInput) -> Dict[str, Any]:
        """
        Execute semantic search.
        
        Args:
            input_data: Search parameters
            
        Returns:
            Search results
        """
        # Initialize connector if not already done
        if not self.connector:
            self.connector = AzureSearchConnector()
            
        # Perform search
        results = self.connector.semantic_search(
            query=input_data.query,
            top_k=input_data.top_k,
            filter=input_data.filters
        )
        
        return {"results": results}


class HybridSearchInput(BaseModel):
    """Input for HybridSearchTool."""
    
    query: str = Field(
        ...,
        description="The search query text",
    )
    top_k: int = Field(
        5,
        description="Number of results to return",
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional filters for search (e.g. {'category': 'troubleshooting'})",
    )


class HybridSearchOutput(BaseModel):
    """Output from HybridSearchTool."""
    
    results: List[Dict[str, Any]] = Field(
        ...,
        description="List of search results with combined ranking from vector and semantic search",
    )


class HybridSearchTool(BaseTool[HybridSearchInput, HybridSearchOutput]):
    """Tool for performing hybrid search combining vector and semantic search."""
    
    name = "hybrid_search"
    description = "Search for information using hybrid search (combining vector and semantic search)"
    input_model = HybridSearchInput
    output_model = HybridSearchOutput
    connector: AzureSearchConnector = None
    
    def __init__(self):
        """Initialize the hybrid search tool."""
        super().__init__()
        self.connector = AzureSearchConnector()
    
    def _execute(self, input_data: HybridSearchInput) -> Dict[str, Any]:
        """
        Execute hybrid search.
        
        Args:
            input_data: Search parameters
            
        Returns:
            Search results
        """
        # Initialize connector if not already done
        if not self.connector:
            self.connector = AzureSearchConnector()
            
        # Perform search
        results = self.connector.hybrid_search(
            query=input_data.query,
            top_k=input_data.top_k,
            filter=input_data.filters
        )
        
        return {"results": results} 