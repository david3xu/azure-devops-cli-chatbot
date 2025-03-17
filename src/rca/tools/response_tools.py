"""
Response generation tools for the RCA system.
Provides RAG-based response generation using Azure OpenAI.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uuid
import time

from src.rca.tools.base_tool import BaseTool
from src.rca.services.llm_service import LLMService, ChatCompletionRequest, ChatMessage


class ResponseInput(BaseModel):
    """Input model for response generation."""
    query: str
    documents: List[Dict[str, Any]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500


class ResponseOutput(BaseModel):
    """Output model for response generation."""
    response: str
    citation_indices: List[int] = Field(default_factory=list)
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    confidence_score: Optional[float] = None


class ResponseGenerationTool(BaseTool[ResponseInput, ResponseOutput]):
    """
    Tool for generating responses using LLM with retrieved documents.
    """
    input_model = ResponseInput
    output_model = ResponseOutput
    name = "response_generation"
    description = "Generate response using LLM with retrieved documents"
    
    def __init__(self):
        """Initialize response generation tool."""
        # Initialize the LLM service
        self.llm_service = LLMService()
        self.llm_service.initialize()
    
    def _execute(self, input_data: ResponseInput) -> Dict[str, Any]:
        """
        Generate a response based on the query and retrieved documents.
        
        Args:
            input_data: Validated input data
            
        Returns:
            Dictionary with generated response and metadata
        """
        # Format documents for prompt
        formatted_documents = ""
        for i, doc in enumerate(input_data.documents):
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("source", "unknown")
            formatted_documents += f"Document {i+1} [source: {source}]: {content}\n\n"
        
        # Create system prompt
        system_prompt = """You are an AI assistant for root cause analysis. 
Use the provided documents to answer the query. 
If the documents don't contain relevant information, say so.
Include citation numbers [1], [2], etc. when referencing specific documents."""

        # Create user prompt with query and documents
        user_prompt = f"""Query: {input_data.query}

Here are the retrieved documents:
{formatted_documents}

Based on these documents, provide a comprehensive answer to the query."""
        
        # Create messages for LLM request
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt)
        ]
        
        # Prepare request
        start_time = time.time()
        request = ChatCompletionRequest(
            messages=messages,
            temperature=input_data.temperature,
            max_tokens=input_data.max_tokens
        )
        
        # Call LLM service
        completion = self.llm_service.chat_completion(request)
        
        # Extract citation indices from response
        # This is a simple implementation - could be more sophisticated
        response_text = completion.content
        citation_indices = []
        
        for i in range(len(input_data.documents)):
            doc_ref = f"[{i+1}]"
            if doc_ref in response_text:
                citation_indices.append(i)
        
        # Calculate confidence (placeholder - could be more sophisticated)
        confidence_score = 0.7  # Default confidence
        if completion.tokens_used > 0:
            confidence_score = min(0.95, 0.5 + (completion.tokens_used / 1000))
        
        # Return formatted output
        return {
            "response": response_text,
            "citation_indices": citation_indices,
            "query_id": str(uuid.uuid4()),  # Generate a unique ID
            "confidence_score": confidence_score,
        } 