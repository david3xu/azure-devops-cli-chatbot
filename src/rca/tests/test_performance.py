"""
Performance benchmarking for the RCA system.
Measures and compares the performance of different search methods.
"""
import os
import sys
import time
import json
import statistics
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

from src.rca.connectors.embeddings import AzureAdaEmbeddingService
from src.rca.connectors.azure_search import AzureSearchConnector
from src.rca.tools.search_tools import VectorSearchTool, SemanticSearchTool, HybridSearchTool
from src.rca.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

class PerformanceBenchmark:
    """Benchmarking tool for measuring system performance."""
    
    def __init__(self):
        """Initialize the benchmark environment."""
        self.results_dir = project_root / "data" / "benchmarks"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.embedding_service = AzureAdaEmbeddingService()
        self.search_connector = AzureSearchConnector(embedding_service=self.embedding_service)
        
        # Initialize tools
        self.vector_search_tool = VectorSearchTool(search_connector=self.search_connector)
        self.semantic_search_tool = SemanticSearchTool(search_connector=self.search_connector)
        self.hybrid_search_tool = HybridSearchTool(search_connector=self.search_connector)
        
        # Benchmark data
        self.test_queries = [
            "How to create a new Azure DevOps project?",
            "What is the difference between Git and Azure Repos?",
            "How to set up CI/CD pipeline in Azure DevOps?",
            "How to troubleshoot build failures in Azure Pipelines?",
            "What are the best practices for organizing Azure DevOps work items?",
            "How to integrate Azure DevOps with Microsoft Teams?",
            "What are the different types of Azure DevOps agents?",
            "How to set up branch policies in Azure Repos?",
            "What is Azure Artifacts and how is it used?",
            "How to migrate from Jenkins to Azure Pipelines?"
        ]
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": self._get_environment_info(),
            "embedding": [],
            "vector_search": [],
            "semantic_search": [],
            "hybrid_search": []
        }
    
    def _get_environment_info(self):
        """Get information about the execution environment."""
        # In a real benchmark, collect more detailed system information
        return {
            "platform": sys.platform,
            "python_version": sys.version,
            "mock_mode": self.search_connector.use_mock
        }
    
    def benchmark_embedding(self, num_runs=3):
        """Benchmark the embedding service."""
        logger.info(f"Benchmarking embedding service with {num_runs} runs per query")
        
        for query in self.test_queries:
            query_results = {
                "query": query,
                "single_embedding": [],
                "batch_embedding": []
            }
            
            # Benchmark single embedding
            for _ in range(num_runs):
                start_time = time.time()
                _ = self.embedding_service.embed_query(query)
                elapsed = time.time() - start_time
                query_results["single_embedding"].append(elapsed)
            
            # Benchmark batch embedding with increasing sizes
            for batch_size in [2, 5, 10]:
                batch_time = []
                for _ in range(num_runs):
                    batch = [query] * batch_size
                    start_time = time.time()
                    _ = self.embedding_service.embed_documents(batch)
                    elapsed = time.time() - start_time
                    batch_time.append(elapsed)
                
                query_results["batch_embedding"].append({
                    "batch_size": batch_size,
                    "avg_time": statistics.mean(batch_time),
                    "min_time": min(batch_time),
                    "max_time": max(batch_time)
                })
            
            self.results["embedding"].append(query_results)
            
            logger.info(f"Query: '{query[:30]}...' - Avg. embedding time: "
                       f"{statistics.mean(query_results['single_embedding']):.4f}s")
    
    def benchmark_vector_search(self, num_runs=3):
        """Benchmark vector search performance."""
        logger.info(f"Benchmarking vector search with {num_runs} runs per query")
        
        for query in self.test_queries:
            query_results = {
                "query": query,
                "top_k_3": [],
                "top_k_5": [],
                "top_k_10": []
            }
            
            # Benchmark with different top_k values
            for top_k in [3, 5, 10]:
                times = []
                for _ in range(num_runs):
                    start_time = time.time()
                    _ = self.vector_search_tool.execute(query=query, top_k=top_k)
                    elapsed = time.time() - start_time
                    times.append(elapsed)
                
                query_results[f"top_k_{top_k}"] = times
            
            self.results["vector_search"].append(query_results)
            
            logger.info(f"Query: '{query[:30]}...' - Avg. vector search time (top_k=3): "
                       f"{statistics.mean(query_results['top_k_3']):.4f}s")
    
    def benchmark_semantic_search(self, num_runs=3):
        """Benchmark semantic search performance."""
        logger.info(f"Benchmarking semantic search with {num_runs} runs per query")
        
        for query in self.test_queries:
            query_results = {
                "query": query,
                "top_k_3": [],
                "top_k_5": [],
                "top_k_10": []
            }
            
            # Benchmark with different top_k values
            for top_k in [3, 5, 10]:
                times = []
                for _ in range(num_runs):
                    start_time = time.time()
                    _ = self.semantic_search_tool.execute(query=query, top_k=top_k)
                    elapsed = time.time() - start_time
                    times.append(elapsed)
                
                query_results[f"top_k_{top_k}"] = times
            
            self.results["semantic_search"].append(query_results)
            
            logger.info(f"Query: '{query[:30]}...' - Avg. semantic search time (top_k=3): "
                       f"{statistics.mean(query_results['top_k_3']):.4f}s")
    
    def benchmark_hybrid_search(self, num_runs=3):
        """Benchmark hybrid search performance."""
        logger.info(f"Benchmarking hybrid search with {num_runs} runs per query")
        
        for query in self.test_queries:
            query_results = {
                "query": query,
                "top_k_3": [],
                "top_k_5": [],
                "top_k_10": []
            }
            
            # Benchmark with different top_k values
            for top_k in [3, 5, 10]:
                times = []
                for _ in range(num_runs):
                    start_time = time.time()
                    _ = self.hybrid_search_tool.execute(query=query, top_k=top_k)
                    elapsed = time.time() - start_time
                    times.append(elapsed)
                
                query_results[f"top_k_{top_k}"] = times
            
            self.results["hybrid_search"].append(query_results)
            
            logger.info(f"Query: '{query[:30]}...' - Avg. hybrid search time (top_k=3): "
                       f"{statistics.mean(query_results['top_k_3']):.4f}s")
    
    def benchmark_all(self, num_runs=3):
        """Run all benchmarks."""
        logger.info(f"Running all benchmarks with {num_runs} runs per test")
        
        self.benchmark_embedding(num_runs)
        self.benchmark_vector_search(num_runs)
        self.benchmark_semantic_search(num_runs)
        self.benchmark_hybrid_search(num_runs)
        
        self._save_results()
        self._generate_summary()
    
    def _save_results(self):
        """Save benchmark results to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"benchmark_{timestamp}.json"
        
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Benchmark results saved to {results_file}")
    
    def _generate_summary(self):
        """Generate a summary of benchmark results."""
        summary = {
            "timestamp": self.results["timestamp"],
            "environment": self.results["environment"],
            "metrics": {
                "embedding": self._summarize_embedding_results(),
                "search": self._summarize_search_results()
            }
        }
        
        # Print summary
        print("\n=== Benchmark Summary ===\n")
        print(f"Environment: {'Mock' if self.search_connector.use_mock else 'Real'} mode\n")
        
        print("Embedding Performance:")
        print(f"  Average single embedding time: {summary['metrics']['embedding']['avg_single_time']:.4f}s")
        for batch in summary["metrics"]["embedding"]["batch_times"]:
            print(f"  Batch size {batch['size']}: {batch['avg_time']:.4f}s "
                 f"({batch['size']/batch['avg_time']:.1f} embeddings/s)")
        
        print("\nSearch Performance (top_k=3):")
        search_types = ["vector_search", "semantic_search", "hybrid_search"]
        for search_type in search_types:
            avg_time = summary["metrics"]["search"][search_type]["avg_time"]
            print(f"  {search_type.replace('_', ' ').title()}: {avg_time:.4f}s")
        
        print("\nPerformance Comparison:")
        fastest = min(
            search_types, 
            key=lambda x: summary["metrics"]["search"][x]["avg_time"]
        )
        print(f"  Fastest search method: {fastest.replace('_', ' ').title()}")
        
        slowest = max(
            search_types, 
            key=lambda x: summary["metrics"]["search"][x]["avg_time"]
        )
        print(f"  Slowest search method: {slowest.replace('_', ' ').title()}")
        
        ratio = (
            summary["metrics"]["search"][slowest]["avg_time"] / 
            summary["metrics"]["search"][fastest]["avg_time"]
        )
        print(f"  Performance ratio (slowest/fastest): {ratio:.2f}x")
    
    def _summarize_embedding_results(self):
        """Summarize embedding benchmark results."""
        all_single_times = []
        for query_result in self.results["embedding"]:
            all_single_times.extend(query_result["single_embedding"])
        
        batch_summaries = []
        # Assuming all queries have the same batch sizes
        batch_entries = self.results["embedding"][0]["batch_embedding"]
        for i, entry in enumerate(batch_entries):
            batch_size = entry["batch_size"]
            all_times = []
            for query_result in self.results["embedding"]:
                all_times.append(query_result["batch_embedding"][i]["avg_time"])
            
            batch_summaries.append({
                "size": batch_size,
                "avg_time": statistics.mean(all_times),
                "min_time": min(all_times),
                "max_time": max(all_times)
            })
        
        return {
            "avg_single_time": statistics.mean(all_single_times),
            "min_single_time": min(all_single_times),
            "max_single_time": max(all_single_times),
            "batch_times": batch_summaries
        }
    
    def _summarize_search_results(self):
        """Summarize search benchmark results."""
        search_types = ["vector_search", "semantic_search", "hybrid_search"]
        summary = {}
        
        for search_type in search_types:
            top_k_3_times = []
            for query_result in self.results[search_type]:
                top_k_3_times.extend(query_result["top_k_3"])
            
            summary[search_type] = {
                "avg_time": statistics.mean(top_k_3_times),
                "min_time": min(top_k_3_times),
                "max_time": max(top_k_3_times)
            }
        
        return summary

def run_benchmark():
    """Run the performance benchmark."""
    print("\n=== Starting Performance Benchmark ===\n")
    
    benchmark = PerformanceBenchmark()
    benchmark.benchmark_all(num_runs=2)  # Using 2 runs for faster execution
    
    print("\n=== Performance Benchmark Completed ===\n")

if __name__ == "__main__":
    run_benchmark() 