"""
Command line interface for the RCA agent.
Allows direct interaction with the RCA system for testing.
"""
import argparse
import json
import time
from typing import Dict, Any

from src.rca.agents.base_agent import RCAAgent
from src.rca.tracking.workflow import WorkflowTracker
from src.rca.tracking.storage import JSONFileStorage


def process_query(query: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Process a query through the RCA agent.
    
    Args:
        query: Question to process
        verbose: Whether to print additional details
        
    Returns:
        Dictionary with response and metadata
    """
    # Start timing
    start_time = time.time()
    
    # Initialize agent with file storage for workflow traces
    tracker = WorkflowTracker()
    tracker.register_storage_backend(JSONFileStorage("traces"))
    agent = RCAAgent(tracker=tracker)
    
    # Process query
    if verbose:
        print(f"Processing query: {query}")
        
    result = agent.process(query)
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Add processing time to result
    result["processing_time_seconds"] = processing_time
    
    return result


def display_result(result: Dict[str, Any], verbose: bool = False):
    """
    Display the result of RCA processing.
    
    Args:
        result: Result dictionary from the agent
        verbose: Whether to print additional details
    """
    print("\n" + "="*80)
    print("RCA RESPONSE:")
    print("="*80)
    print(result["response"])
    print("-"*80)
    
    # Display citations
    if "citation_indices" in result and result["citation_indices"]:
        print("SOURCES:")
        for idx in result["citation_indices"]:
            if idx < len(result.get("documents", [])):
                doc = result["documents"][idx]
                print(f"- Document {idx+1}: {doc.get('id', f'doc{idx}')}")
        print("-"*80)
    
    # Display processing time
    print(f"Processing time: {result.get('processing_time_seconds', 0):.2f} seconds")
    
    # Display trace information
    if "trace_id" in result:
        print(f"Trace ID: {result['trace_id']}")
        print("To view detailed trace information:")
        print(f"  - Start server: uvicorn src.main:app --reload")
        print(f"  - Visit: http://localhost:8000/rca/visualize/trace/{result['trace_id']}")
        print("-"*80)
    
    # Display additional details in verbose mode
    if verbose:
        print("\nFULL RESULT:")
        print(json.dumps(result, indent=2, default=str))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="RCA Agent CLI")
    parser.add_argument("query", nargs="?", help="Query to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose output")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        print("RCA Agent CLI - Interactive Mode")
        print("Type 'exit' or 'quit' to end the session")
        
        while True:
            # Get user input
            query = input("\nEnter query: ")
            
            # Check for exit command
            if query.lower() in ["exit", "quit"]:
                break
                
            # Process query
            result = process_query(query, args.verbose)
            
            # Display result
            display_result(result, args.verbose)
    
    elif args.query:
        # Process single query
        result = process_query(args.query, args.verbose)
        
        # Display result
        display_result(result, args.verbose)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 