"""
Search tools for the RCA system.
Provides search tools using Azure AI Search with vector, semantic, and hybrid search.
"""
from typing import Dict, List, Optional, Any
from pydantic import Field

from src.rca.tools.base_tool import BaseTool
from src.rca.connectors.azure_search import AzureSearchConnector


class VectorSearchInput(BaseTool.Input):
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


class VectorSearchOutput(BaseTool.Output):
    """Output from VectorSearchTool."""
    
    results: List[Dict[str, Any]] = Field(
        ...,
        description="List of search results",
    )


class VectorSearchTool(BaseTool):
    """Tool for performing vector search."""
    
    name = "vector_search"
    description = "Search for information using vector search"
    input_class = VectorSearchInput
    output_class = VectorSearchOutput
    connector: AzureSearchConnector = None
    
    def __init__(self):
        """Initialize the vector search tool."""
        super().__init__()
        self.connector = AzureSearchConnector()
    
    def _run(self, input_data: VectorSearchInput) -> VectorSearchOutput:
        """
        Run the vector search tool.
        
        Args:
            input_data: VectorSearchInput
            
        Returns:
            VectorSearchOutput
        """
        # Ensure the connector is initialized
        if not hasattr(self.connector, 'initialized') or not self.connector.initialized:
            self.connector.initialize()
            
        # Perform vector search
        results = self.connector.vector_search(
            query=input_data.query,
            top_k=input_data.top_k,
            filters=input_data.filters,
        )
        
        return VectorSearchOutput(results=results)


class SemanticSearchInput(BaseTool.Input):
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


class SemanticSearchOutput(BaseTool.Output):
    """Output from SemanticSearchTool."""
    
    results: List[Dict[str, Any]] = Field(
        ...,
        description="List of search results with semantic captions",
    )


class SemanticSearchTool(BaseTool):
    """Tool for performing semantic search."""
    
    name = "semantic_search"
    description = "Search for information using semantic search with extractive captions"
    input_class = SemanticSearchInput
    output_class = SemanticSearchOutput
    connector: AzureSearchConnector = None
    
    def __init__(self):
        """Initialize the semantic search tool."""
        super().__init__()
        self.connector = AzureSearchConnector()
    
    def _run(self, input_data: SemanticSearchInput) -> SemanticSearchOutput:
        """
        Run the semantic search tool.
        
        Args:
            input_data: SemanticSearchInput
            
        Returns:
            SemanticSearchOutput
        """
        # Ensure the connector is initialized
        if not hasattr(self.connector, 'initialized') or not self.connector.initialized:
            self.connector.initialize()
            
        # Perform semantic search
        results = self.connector.semantic_search(
            query=input_data.query,
            top_k=input_data.top_k,
            filters=input_data.filters,
        )
        
        return SemanticSearchOutput(results=results)


class HybridSearchInput(BaseTool.Input):
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


class HybridSearchOutput(BaseTool.Output):
    """Output from HybridSearchTool."""
    
    results: List[Dict[str, Any]] = Field(
        ...,
        description="List of search results with combined ranking from vector and semantic search",
    )


class HybridSearchTool(BaseTool):
    """Tool for performing hybrid search combining vector and semantic search."""
    
    name = "hybrid_search"
    description = "Search for information using hybrid search (combining vector and semantic search)"
    input_class = HybridSearchInput
    output_class = HybridSearchOutput
    connector: AzureSearchConnector = None
    
    def __init__(self):
        """Initialize the hybrid search tool."""
        super().__init__()
        self.connector = AzureSearchConnector()
    
    def _run(self, input_data: HybridSearchInput) -> HybridSearchOutput:
        """
        Run the hybrid search tool.
        
        Args:
            input_data: HybridSearchInput
            
        Returns:
            HybridSearchOutput
        """
        # Ensure the connector is initialized
        if not hasattr(self.connector, 'initialized') or not self.connector.initialized:
            self.connector.initialize()
            
        # Perform hybrid search
        results = self.connector.hybrid_search(
            query=input_data.query,
            top_k=input_data.top_k,
            filters=input_data.filters,
        )
        
        return HybridSearchOutput(results=results) 