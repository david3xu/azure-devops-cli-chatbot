"""
Document models for the RCA system.
Contains classes for representing documents and their metadata.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class Document(BaseModel):
    """
    Represents a document in the RCA system.
    Contains content and metadata for retrieval and ranking.
    """
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None
    
    def __str__(self) -> str:
        """String representation of a document."""
        return f"Document(id={self.id}, score={self.score})"


class DocumentCollection(BaseModel):
    """
    Collection of documents with utility methods.
    """
    documents: List[Document] = Field(default_factory=list)
    
    def sort_by_score(self, descending: bool = True) -> 'DocumentCollection':
        """
        Sort documents by score.
        
        Args:
            descending: Whether to sort in descending order
            
        Returns:
            DocumentCollection with sorted documents
        """
        sorted_docs = sorted(
            self.documents, 
            key=lambda x: x.score if x.score is not None else 0.0,
            reverse=descending
        )
        return DocumentCollection(documents=sorted_docs)
    
    def get_top_k(self, k: int) -> 'DocumentCollection':
        """
        Get top k documents by score.
        
        Args:
            k: Number of documents to return
            
        Returns:
            DocumentCollection with top k documents
        """
        return DocumentCollection(documents=self.documents[:k])
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Convert documents to a list of dictionaries.
        
        Returns:
            List of document dictionaries
        """
        return [doc.dict() for doc in self.documents] 