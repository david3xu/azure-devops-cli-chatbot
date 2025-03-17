"""
Evaluation utilities for the RCA search system.
Provides tools to benchmark and evaluate search quality and performance.
"""
from typing import List, Dict, Any, Optional, Union, Tuple
import time
import statistics
import json
import os
from datetime import datetime

from src.rca.utils.logging import get_logger
from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.connectors.embeddings import AzureAdaEmbeddingService

# Configure logger
logger = get_logger(__name__)


class SearchEvaluator:
    """
    Evaluator for search services.
    Benchmarks and compares vector, semantic, and hybrid search approaches.
    """
    
    def __init__(self):
        """Initialize the search evaluator."""
        self.search_connector = AzureSearchConnector()
        self.embedding_service = AzureAdaEmbeddingService()
        
        # Ensure services are initialized
        self.initialized = False
        
        # For storing evaluation results
        self.results_dir = os.path.join("data", "evaluation")
        os.makedirs(self.results_dir, exist_ok=True)
    
    def initialize(self) -> bool:
        """
        Initialize the evaluator and its dependencies.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.initialized:
            return True
            
        # Initialize services
        embedding_initialized = self.embedding_service.initialize()
        search_initialized = self.search_connector.initialize()
        
        self.initialized = embedding_initialized and search_initialized
        
        if not self.initialized:
            logger.error("Failed to initialize search evaluator dependencies")
            if not embedding_initialized:
                logger.error("Embedding service initialization failed")
            if not search_initialized:
                logger.error("Search connector initialization failed")
        
        return self.initialized
    
    def evaluate_query(
        self, 
        query: str,
        expected_results: Optional[List[str]] = None,
        top_k: int = 5,
        run_count: int = 3
    ) -> Dict[str, Any]:
        """
        Evaluate a single query using different search methods.
        
        Args:
            query: The query to evaluate
            expected_results: Optional list of expected document IDs
            top_k: Number of results to retrieve
            run_count: Number of times to run each method for timing
            
        Returns:
            Evaluation results
        """
        if not self.initialized and not self.initialize():
            logger.error("Failed to initialize search evaluator")
            return {"error": "Failed to initialize search evaluator"}
        
        results = {
            "query": query,
            "top_k": top_k,
            "timestamp": datetime.now().isoformat(),
            "methods": {},
        }
        
        # Evaluate vector search
        vector_results, vector_metrics = self._benchmark_search_method(
            method_name="vector",
            search_fn=self.search_connector.vector_search,
            query=query,
            top_k=top_k,
            expected_results=expected_results,
            run_count=run_count
        )
        results["methods"]["vector"] = {
            "metrics": vector_metrics,
            "results": vector_results
        }
        
        # Evaluate semantic search
        semantic_results, semantic_metrics = self._benchmark_search_method(
            method_name="semantic",
            search_fn=self.search_connector.semantic_search,
            query=query,
            top_k=top_k,
            expected_results=expected_results,
            run_count=run_count
        )
        results["methods"]["semantic"] = {
            "metrics": semantic_metrics,
            "results": semantic_results
        }
        
        # Evaluate hybrid search
        hybrid_results, hybrid_metrics = self._benchmark_search_method(
            method_name="hybrid",
            search_fn=self.search_connector.hybrid_search,
            query=query,
            top_k=top_k,
            expected_results=expected_results,
            run_count=run_count
        )
        results["methods"]["hybrid"] = {
            "metrics": hybrid_metrics,
            "results": hybrid_results
        }
        
        # Calculate overall recommendations
        best_method = self._determine_best_method(results["methods"])
        results["best_method"] = best_method
        
        # Save results
        self._save_evaluation_results(query, results)
        
        return results
    
    def _benchmark_search_method(
        self,
        method_name: str,
        search_fn: callable,
        query: str,
        top_k: int,
        expected_results: Optional[List[str]] = None,
        run_count: int = 3
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Benchmark a specific search method.
        
        Args:
            method_name: Name of the search method
            search_fn: Search function to call
            query: Query string
            top_k: Number of results to retrieve
            expected_results: Optional list of expected document IDs
            run_count: Number of times to run for timing
            
        Returns:
            Tuple of (results, metrics)
        """
        logger.info(f"Benchmarking {method_name} search for query: '{query}'")
        
        # Run multiple times for timing metrics
        latencies = []
        for i in range(run_count):
            start_time = time.time()
            results = search_fn(query=query, top_k=top_k)
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # ms
            latencies.append(latency)
            
            # Only need to save results once
            if i == 0:
                search_results = results
        
        # Calculate relevance metrics if expected results provided
        relevance_metrics = {}
        if expected_results:
            retrieved_ids = [doc.get("id", "") for doc in search_results]
            
            # Calculate precision
            relevant_retrieved = sum(1 for doc_id in retrieved_ids if doc_id in expected_results)
            precision = relevant_retrieved / len(retrieved_ids) if retrieved_ids else 0
            
            # Calculate recall
            recall = relevant_retrieved / len(expected_results) if expected_results else 0
            
            # Calculate F1
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            relevance_metrics = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "relevant_retrieved": relevant_retrieved,
                "total_relevant": len(expected_results),
            }
        
        # Calculate timing metrics
        timing_metrics = {
            "mean_latency_ms": statistics.mean(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "stddev_latency_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
        }
        
        # Combine metrics
        metrics = {
            **timing_metrics,
            **(relevance_metrics if relevance_metrics else {})
        }
        
        return search_results, metrics
    
    def _determine_best_method(self, methods_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the best search method based on metrics.
        
        Args:
            methods_results: Results from all methods
            
        Returns:
            Best method information
        """
        best_method = {
            "for_performance": None,
            "for_relevance": None,
            "overall": None,
            "notes": []
        }
        
        # Find fastest method
        latencies = {
            method: data["metrics"].get("mean_latency_ms", float("inf"))
            for method, data in methods_results.items()
        }
        best_for_performance = min(latencies.items(), key=lambda x: x[1])[0]
        best_method["for_performance"] = best_for_performance
        
        # Find most relevant method if relevance metrics available
        if "f1" in next(iter(methods_results.values()))["metrics"]:
            f1_scores = {
                method: data["metrics"].get("f1", 0)
                for method, data in methods_results.items()
            }
            best_for_relevance = max(f1_scores.items(), key=lambda x: x[1])[0]
            best_method["for_relevance"] = best_for_relevance
            
            # Determine overall best with bias toward relevance
            best_method["overall"] = best_for_relevance
            
            # Add notes about the trade-offs
            perf_diff = latencies[best_for_relevance] - latencies[best_for_performance]
            if perf_diff > 50:  # More than 50ms difference
                best_method["notes"].append(
                    f"{best_for_relevance} search is {perf_diff:.1f}ms slower than {best_for_performance} search "
                    f"but has better relevance"
                )
        else:
            # If no relevance metrics, use performance as deciding factor
            best_method["overall"] = best_for_performance
        
        return best_method
    
    def _save_evaluation_results(self, query: str, results: Dict[str, Any]) -> None:
        """
        Save evaluation results to disk.
        
        Args:
            query: The query that was evaluated
            results: Evaluation results
        """
        # Create a filename based on timestamp and query
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_slug = "".join(c if c.isalnum() else "_" for c in query)[:30]
        filename = f"{timestamp}_{query_slug}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Saved evaluation results to {filepath}")
    
    def evaluate_test_set(self, test_file: str) -> Dict[str, Any]:
        """
        Evaluate a set of test queries from a file.
        
        Args:
            test_file: Path to test file (JSON format)
            
        Returns:
            Aggregated evaluation results
        """
        if not os.path.exists(test_file):
            logger.error(f"Test file not found: {test_file}")
            return {"error": f"Test file not found: {test_file}"}
            
        try:
            with open(test_file, "r") as f:
                test_data = json.load(f)
                
            if not isinstance(test_data, list):
                logger.error(f"Invalid test data format. Expected a list of test cases.")
                return {"error": "Invalid test data format"}
                
            # Validate test data structure
            for i, test_case in enumerate(test_data):
                if "query" not in test_case:
                    logger.error(f"Test case {i} missing 'query' field")
                    return {"error": f"Test case {i} missing 'query' field"}
            
            # Run evaluation for each test case
            results = []
            for test_case in test_data:
                query = test_case["query"]
                expected_results = test_case.get("expected_results")
                top_k = test_case.get("top_k", 5)
                
                eval_result = self.evaluate_query(
                    query=query,
                    expected_results=expected_results,
                    top_k=top_k
                )
                results.append(eval_result)
            
            # Aggregate results
            aggregated = self._aggregate_results(results)
            
            # Save aggregated results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_test_set_results.json"
            filepath = os.path.join(self.results_dir, filename)
            
            with open(filepath, "w") as f:
                json.dump({"individual_results": results, "aggregated": aggregated}, f, indent=2)
                
            logger.info(f"Saved test set evaluation results to {filepath}")
            
            return {
                "individual_results": results,
                "aggregated": aggregated
            }
                
        except Exception as e:
            logger.error(f"Error evaluating test set: {str(e)}")
            return {"error": f"Error evaluating test set: {str(e)}"}
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results from multiple evaluations.
        
        Args:
            results: List of individual evaluation results
            
        Returns:
            Aggregated metrics
        """
        aggregated = {
            "methods": {},
            "query_count": len(results),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Initialize method aggregates
        method_names = results[0]["methods"].keys()
        for method in method_names:
            aggregated["methods"][method] = {
                "mean_latency_ms": [],
                "precision": [],
                "recall": [],
                "f1": []
            }
        
        # Collect metrics from all results
        for result in results:
            for method, data in result["methods"].items():
                metrics = data["metrics"]
                
                # Add latency
                aggregated["methods"][method]["mean_latency_ms"].append(metrics["mean_latency_ms"])
                
                # Add relevance metrics if available
                if "precision" in metrics:
                    aggregated["methods"][method]["precision"].append(metrics["precision"])
                    aggregated["methods"][method]["recall"].append(metrics["recall"])
                    aggregated["methods"][method]["f1"].append(metrics["f1"])
        
        # Calculate averages
        for method in method_names:
            # Calculate average latency
            latencies = aggregated["methods"][method]["mean_latency_ms"]
            aggregated["methods"][method]["avg_latency_ms"] = statistics.mean(latencies)
            
            # Calculate average relevance metrics if available
            if aggregated["methods"][method]["precision"]:
                precisions = aggregated["methods"][method]["precision"]
                recalls = aggregated["methods"][method]["recall"]
                f1s = aggregated["methods"][method]["f1"]
                
                aggregated["methods"][method]["avg_precision"] = statistics.mean(precisions)
                aggregated["methods"][method]["avg_recall"] = statistics.mean(recalls)
                aggregated["methods"][method]["avg_f1"] = statistics.mean(f1s)
        
        # Determine best method overall
        if "avg_f1" in next(iter(aggregated["methods"].values())):
            # If we have relevance metrics, prioritize F1 score
            best_method = max(
                aggregated["methods"].items(),
                key=lambda x: x[1]["avg_f1"]
            )[0]
        else:
            # Otherwise prioritize performance
            best_method = min(
                aggregated["methods"].items(),
                key=lambda x: x[1]["avg_latency_ms"]
            )[0]
            
        aggregated["best_method"] = best_method
        
        return aggregated


def create_test_set(output_file: str, queries: List[Dict[str, Any]]) -> bool:
    """
    Create a test set file for evaluation.
    
    Args:
        output_file: Path to save the test set
        queries: List of query dictionaries with format:
                 {"query": "...", "expected_results": ["id1", "id2"], "top_k": 5}
                 
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Write test set to file
        with open(output_file, "w") as f:
            json.dump(queries, f, indent=2)
            
        logger.info(f"Created test set with {len(queries)} queries at {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating test set: {str(e)}")
        return False 