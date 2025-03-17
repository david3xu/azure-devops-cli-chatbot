"""
Base agent implementation for RCA system.
Provides orchestration of tools with input/output validation.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

from src.rca.tracking.workflow import WorkflowTracker


class AgentState(BaseModel):
    """
    Represents the current state of the agent during processing.
    Tracks query, retrieved documents, and processing history.
    """
    query: str
    context: Optional[List[Dict[str, Any]]] = None
    tools_used: List[str] = Field(default_factory=list)
    

class RCAAgent:
    """
    Root Cause Analysis agent that orchestrates the RAG process.
    Manages tool selection, execution, and response generation.
    """
    def __init__(self, tools=None, tracker: Optional[WorkflowTracker] = None):
        """
        Initialize the RCA agent with tools and workflow tracker.
        
        Args:
            tools: Dictionary of tool instances. If None, default tools are used.
            tracker: WorkflowTracker instance. If None, one will be created.
        """
        self.tools = tools or self._get_default_tools()
        self.tracker = tracker or WorkflowTracker()
        
    def _get_default_tools(self) -> Dict[str, Any]:
        """
        Get the default set of tools for the agent.
        
        Returns:
            Dictionary of tool instances
        """
        from src.rca.tools.search_tools import VectorSearchTool
        from src.rca.tools.document_tools import DocumentRankingTool
        from src.rca.tools.response_tools import ResponseGenerationTool
        
        return {
            "vector_search": VectorSearchTool(),
            "document_ranking": DocumentRankingTool(),
            "response_generation": ResponseGenerationTool()
        }
        
    def process(self, query: str) -> Dict[str, Any]:
        """
        Process a query using the RAG pipeline with workflow tracking.
        
        Args:
            query: User's question
            
        Returns:
            Dictionary with response and metadata including trace_id
        """
        # Start tracking the workflow
        trace_id = self.tracker.start_trace(query)
        
        # 1. Create initial state
        state = AgentState(query=query)
        
        try:
            # 2. Run vector search
            search_inputs = {"query": query}
            self.tracker.track_step(
                trace_id=trace_id,
                step_name="vector_search",
                inputs=search_inputs,
                outputs={},  # Will be filled in after execution
                metadata={"tool_name": "vector_search"}
            )
            
            search_results = self.tools["vector_search"].execute(query=query)
            
            # Update step with outputs
            self.tracker.track_step(
                trace_id=trace_id,
                step_name="vector_search",
                inputs=search_inputs,
                outputs={"documents": search_results.results},
                metadata={
                    "tool_name": "vector_search", 
                    "document_count": len(search_results.results)
                }
            )
            
            state.context = search_results.results
            state.tools_used.append("vector_search")
            
            # 3. Rank documents
            ranking_inputs = {
                "query": query, 
                "documents": search_results.results
            }
            
            self.tracker.track_step(
                trace_id=trace_id,
                step_name="document_ranking",
                inputs=ranking_inputs,
                outputs={},
                metadata={"tool_name": "document_ranking"}
            )
            
            ranked_docs = self.tools["document_ranking"].execute(**ranking_inputs)
            
            self.tracker.track_step(
                trace_id=trace_id,
                step_name="document_ranking",
                inputs=ranking_inputs,
                outputs={"documents": ranked_docs.results},
                metadata={
                    "tool_name": "document_ranking",
                    "document_count": len(ranked_docs.results)
                }
            )
            
            state.context = ranked_docs.results
            state.tools_used.append("document_ranking")
            
            # 4. Generate response
            response_inputs = {
                "query": query,
                "documents": ranked_docs.results
            }
            
            self.tracker.track_step(
                trace_id=trace_id,
                step_name="response_generation",
                inputs=response_inputs,
                outputs={},
                metadata={"tool_name": "response_generation"}
            )
            
            response_result = self.tools["response_generation"].execute(**response_inputs)
            
            self.tracker.track_step(
                trace_id=trace_id,
                step_name="response_generation",
                inputs=response_inputs,
                outputs={"response": response_result.response},
                metadata={"tool_name": "response_generation"}
            )
            
            # 5. Prepare output
            output = {
                "query": query,
                "trace_id": trace_id,
                "response": response_result.response,
                "citation_indices": response_result.citation_indices,
                "documents": ranked_docs.results,
                "confidence_score": response_result.confidence_score or 0.0
            }
            
            # Complete the trace
            self.tracker.complete_trace(trace_id, response_result.response)
            
            return output
            
        except Exception as e:
            # Track the error
            self.tracker.track_step(
                trace_id=trace_id,
                step_name="error",
                inputs={"query": query},
                outputs={"error": str(e)},
                metadata={
                    "error_type": type(e).__name__,
                    "tools_used": state.tools_used
                }
            )
            
            # Complete the trace with error information
            self.tracker.complete_trace(trace_id, f"Error: {str(e)}")
            
            # Re-raise the exception
            raise 