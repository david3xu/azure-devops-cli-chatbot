"""
Document processing tools for the RCA system.
Provides document ranking capabilities.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

from src.rca.tools.base_tool import BaseTool


class RankingInput(BaseModel):
    """Input model for document ranking."""
    query: str
    documents: List[Dict[str, Any]]


class RankingOutput(BaseModel):
    """Output model for document ranking."""
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    original_query: str


class DocumentRankingTool(BaseTool[RankingInput, RankingOutput]):
    """
    Tool for ranking documents based on relevance to the query.
    For Milestone 1, this is a simple ranking based on the score from vector search.
    In future milestones, this would incorporate more sophisticated ranking algorithms.
    """
    input_model = RankingInput
    output_model = RankingOutput
    name = "document_ranking"
    description = "Rank documents by relevance to the query"
    
    def _execute(self, input_data: RankingInput) -> Dict[str, Any]:
        """
        Rank documents by relevance to the query.
        
        Args:
            input_data: Validated ranking input
            
        Returns:
            Dictionary with ranked documents
        """
        # For Milestone 1, we simply sort by the score field
        # In future milestones, this would use more sophisticated ranking
        
        # Sort documents by score (descending)
        sorted_docs = sorted(
            input_data.documents,
            key=lambda x: x.get("score", 0),
            reverse=True
        )
        
        return {
            "documents": sorted_docs,
            "original_query": input_data.query
        } 