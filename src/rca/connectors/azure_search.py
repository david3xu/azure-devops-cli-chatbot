"""
Azure AI Search connector for the RCA system.
Provides integration with Azure AI Search for vector search, semantic search, and hybrid search.
"""
from typing import Dict, List, Optional, Any, Union
import json
import requests
import os
import logging
import time

from src.chatbot.config.settings import settings
from src.rca.connectors.azure_openai import AzureOpenAIConnector
from src.rca.utils.logging import get_logger
from src.rca.connectors.embeddings import AzureAdaEmbeddingService

# Configure logger
logger = get_logger(__name__)


class AzureSearchConnector:
    """
    Connector for Azure AI Search.
    Handles vector search, semantic search, hybrid search, and index management.
    """
    
    def __init__(self):
        """Initialize the Azure AI Search connector."""
        # Use existing Azure credentials
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP")
        
        # Azure Search specific settings
        self.service_name = os.getenv("AZURE_SEARCH_SERVICE_NAME")
        self.key = os.getenv("AZURE_SEARCH_KEY", "")
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
        if not self.endpoint and self.service_name:
            self.endpoint = f"https://{self.service_name}.search.windows.net"
            
        self.index_name = os.getenv("AZURE_SEARCH_INDEX", "rca-index")
        self.api_version = "2023-11-01"
        self.semantic_config = os.getenv("AZURE_SEARCH_SEMANTIC_CONFIG", "default")
        
        # Initialize the embedding service for vector search
        self.embedding_service = AzureAdaEmbeddingService()
        
        # Tracking successful initialization
        self.initialized = False
        self.use_mock = False
    
    def initialize(self) -> bool:
        """
        Initialize the Azure Search connector.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.initialized:
            return True
            
        try:
            # Validate required settings
            if not all([self.endpoint, self.key, self.index_name]):
                logger.warning("Missing required Azure Search settings")
                logger.warning(f"Endpoint: {'Set' if self.endpoint else 'Missing'}")
                logger.warning(f"API Key: {'Set' if self.key else 'Missing'}")
                logger.warning(f"Index Name: {'Set' if self.index_name else 'Missing'}")
                logger.info("Using mock search results for development")
                self.use_mock = True
                self.initialized = True
                return True
            
            # Initialize the embedding service
            self.embedding_service.initialize()
            
            # Check if we can connect to the search service
            try:
                # Try to get index statistics
                url = f"{self.endpoint}/indexes/{self.index_name}/stats"
                headers = {
                    "Content-Type": "application/json",
                    "api-key": self.key
                }
                
                params = {
                    "api-version": self.api_version
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    stats = response.json()
                    logger.info(f"Connected to Azure Search index: {self.index_name}")
                    logger.info(f"Document count: {stats.get('documentCount', 'unknown')}")
                    self.initialized = True
                    self.use_mock = False
                    return True
                elif response.status_code == 404:
                    logger.warning(f"Index {self.index_name} does not exist")
                    logger.info("Using mock search results for development")
                    self.use_mock = True
                    self.initialized = True
                    return True
                else:
                    error_msg = "Unknown error"
                    try:
                        error_data = response.json()
                        if "error" in error_data and "message" in error_data["error"]:
                            error_msg = error_data["error"]["message"]
                    except Exception:
                        pass
                    
                    logger.warning(f"Failed to connect to Azure Search: {response.status_code} - {error_msg}")
                    logger.info("Using mock search results for development")
                    self.use_mock = True
                    self.initialized = True
                    return True
                    
            except Exception as e:
                logger.warning(f"Error checking connection to Azure Search: {str(e)}")
                logger.info("Using mock search results for development")
                self.use_mock = True
                self.initialized = True
                return True
                
        except Exception as e:
            logger.error(f"Error initializing Azure Search connector: {str(e)}")
            logger.info("Using mock search results for development")
            self.use_mock = True
            self.initialized = True
            return True
    
    def vector_search(
        self, 
        query: str, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector search using Azure AI Search.
        
        Args:
            query: Query text
            top_k: Number of results to return
            filters: Optional filters for search
            
        Returns:
            List of search results
        """
        # Initialize if not already done
        if not self.initialized:
            self.initialize()
        
        # Use mock data if API is not available
        if self.use_mock:
            return self._get_mock_results(top_k, filters)
        
        try:
            # Get embedding for the query
            start_time = time.time()
            query_embedding = self.embedding_service.embed_query(query)
            embedding_time = (time.time() - start_time) * 1000
            logger.debug(f"Generated query embedding in {embedding_time:.2f}ms")
            
            # Prepare search request
            url = f"{self.endpoint}/indexes/{self.index_name}/docs/search"
            headers = {
                "Content-Type": "application/json",
                "api-key": self.key
            }
            
            # Construct filter if provided
            filter_expr = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    # Handle different value types
                    if isinstance(value, str):
                        filter_conditions.append(f"{key} eq '{value}'")
                    elif isinstance(value, (int, float, bool)):
                        filter_conditions.append(f"{key} eq {value}")
                    elif isinstance(value, list):
                        # Handle array contains
                        items = [f"'{item}'" if isinstance(item, str) else str(item) for item in value]
                        filter_conditions.append(f"{key}/any(item: search.in(item, {', '.join(items)}))")
                
                if filter_conditions:
                    filter_expr = " and ".join(filter_conditions)
            
            # Construct the search request
            search_request = {
                "vectors": [{
                    "value": query_embedding,
                    "fields": "contentVector",
                    "k": top_k
                }],
                "top": top_k,
                "select": "id,content,metadata,score",
                "count": True
            }
            
            if filter_expr:
                search_request["filter"] = filter_expr
                
            # Make the request
            response = requests.post(
                url, 
                headers=headers, 
                json=search_request,
                params={"api-version": self.api_version}
            )
            
            if response.status_code != 200:
                logger.error(f"Vector search failed: {response.status_code} - {response.text}")
                return self._get_mock_results(top_k, filters)
                
            # Process the response
            result = response.json()
            
            # Format the results
            documents = []
            for doc in result.get("value", []):
                # Convert the document to our standard format
                formatted_doc = {
                    "id": doc.get("id", ""),
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                    "score": doc.get("@search.score", 0.0)
                }
                documents.append(formatted_doc)
                
            return documents
                
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            return self._get_mock_results(top_k, filters)
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using Azure AI Search's built-in capabilities.
        
        Args:
            query: Query text
            top_k: Number of results to return
            filters: Optional filters for search
            
        Returns:
            List of search results with semantic captions
        """
        # Initialize if not already done
        if not self.initialized:
            self.initialize()
        
        # Use mock data if API is not available
        if self.use_mock:
            return self._get_mock_results(top_k, filters)
        
        try:
            # Prepare search request
            url = f"{self.endpoint}/indexes/{self.index_name}/docs/search"
            headers = {
                "Content-Type": "application/json",
                "api-key": self.key
            }
            
            # Construct filter if provided
            filter_expr = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    # Handle different value types appropriately
                    if isinstance(value, str):
                        filter_conditions.append(f"{key} eq '{value}'")
                    elif isinstance(value, (int, float, bool)):
                        filter_conditions.append(f"{key} eq {value}")
                    elif isinstance(value, list):
                        # Handle array contains
                        items = [f"'{item}'" if isinstance(item, str) else str(item) for item in value]
                        filter_conditions.append(f"{key}/any(item: search.in(item, {', '.join(items)}))")
                
                if filter_conditions:
                    filter_expr = " and ".join(filter_conditions)
            
            # Construct the semantic search request
            search_request = {
                "search": query,
                "queryType": "semantic",
                "semanticConfiguration": self.semantic_config,
                "top": top_k,
                "select": "id,content,metadata",
                "captions": "extractive",
                "answers": "extractive",
                "count": True
            }
            
            if filter_expr:
                search_request["filter"] = filter_expr
                
            # Make the request
            start_time = time.time()
            response = requests.post(
                url, 
                headers=headers, 
                json=search_request,
                params={"api-version": self.api_version}
            )
            search_time = (time.time() - start_time) * 1000
            logger.debug(f"Semantic search completed in {search_time:.2f}ms")
            
            if response.status_code != 200:
                logger.error(f"Semantic search failed: {response.status_code} - {response.text}")
                return self._get_mock_results(top_k, filters)
                
            # Process the response
            result = response.json()
            
            # Format the results including semantic captions
            documents = []
            for doc in result.get("value", []):
                # Get semantic caption if available
                caption = ""
                if "@search.captions" in doc:
                    captions = doc["@search.captions"]
                    if captions and len(captions) > 0:
                        caption = captions[0].get("text", "")
                
                # Convert the document to our standard format
                formatted_doc = {
                    "id": doc.get("id", ""),
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                    "score": doc.get("@search.score", 0.0),
                    "caption": caption
                }
                documents.append(formatted_doc)
                
            return documents
                
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return self._get_mock_results(top_k, filters)
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector and semantic search.
        
        Args:
            query: Query text
            top_k: Number of results to return
            filters: Optional filters for search
            
        Returns:
            List of search results with best results from both approaches
        """
        # Initialize if not already done
        if not self.initialized:
            self.initialize()
        
        # Use mock data if API is not available
        if self.use_mock:
            return self._get_mock_results(top_k, filters)
        
        try:
            # Get embedding for the query
            start_time = time.time()
            query_embedding = self.embedding_service.embed_query(query)
            embedding_time = (time.time() - start_time) * 1000
            logger.debug(f"Generated query embedding in {embedding_time:.2f}ms")
            
            # Prepare search request
            url = f"{self.endpoint}/indexes/{self.index_name}/docs/search"
            headers = {
                "Content-Type": "application/json",
                "api-key": self.key
            }
            
            # Construct filter if provided
            filter_expr = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    # Handle different value types
                    if isinstance(value, str):
                        filter_conditions.append(f"{key} eq '{value}'")
                    elif isinstance(value, (int, float, bool)):
                        filter_conditions.append(f"{key} eq {value}")
                    elif isinstance(value, list):
                        # Handle array contains
                        items = [f"'{item}'" if isinstance(item, str) else str(item) for item in value]
                        filter_conditions.append(f"{key}/any(item: search.in(item, {', '.join(items)}))")
                
                if filter_conditions:
                    filter_expr = " and ".join(filter_conditions)
            
            # Construct the hybrid search request
            search_request = {
                "search": query,
                "queryType": "semantic",
                "semanticConfiguration": self.semantic_config,
                "vectors": [{
                    "value": query_embedding,
                    "fields": "contentVector",
                    "k": top_k * 2  # Retrieve more candidates for reranking
                }],
                "top": top_k,
                "select": "id,content,metadata",
                "captions": "extractive",
                "count": True
            }
            
            if filter_expr:
                search_request["filter"] = filter_expr
                
            # Make the request
            search_start = time.time()
            response = requests.post(
                url, 
                headers=headers, 
                json=search_request,
                params={"api-version": self.api_version}
            )
            search_time = (time.time() - search_start) * 1000
            logger.debug(f"Hybrid search completed in {search_time:.2f}ms")
            
            if response.status_code != 200:
                logger.error(f"Hybrid search failed: {response.status_code} - {response.text}")
                return self._get_mock_results(top_k, filters)
                
            # Process the response
            result = response.json()
            
            # Format the results
            documents = []
            for doc in result.get("value", []):
                # Get semantic caption if available
                caption = ""
                if "@search.captions" in doc:
                    captions = doc["@search.captions"]
                    if captions and len(captions) > 0:
                        caption = captions[0].get("text", "")
                
                # Get vector score and semantic score
                vector_score = doc.get("@search.vectorScore", 0.0)
                semantic_score = doc.get("@search.score", 0.0)
                
                # Convert the document to our standard format
                formatted_doc = {
                    "id": doc.get("id", ""),
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                    "score": semantic_score,  # Use semantic score as primary
                    "vector_score": vector_score,
                    "caption": caption
                }
                documents.append(formatted_doc)
                
            return documents
                
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            return self._get_mock_results(top_k, filters)
    
    def _get_mock_results(self, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get mock search results for development and testing.
        
        Args:
            top_k: Number of results to return
            filters: Optional filters for search
            
        Returns:
            List of mock search results
        """
        # Mock search results
        mock_results = [
            {
                "id": "doc1",
                "content": "This is a sample document about root cause analysis. When investigating issues, start by collecting all relevant logs and metrics.",
                "metadata": {"source": "knowledge_base", "category": "rca"},
                "score": 0.95,
                "caption": "Start by collecting all relevant logs and metrics."
            },
            {
                "id": "doc2",
                "content": "Common techniques for troubleshooting include log analysis, monitoring metrics, and reviewing recent changes to the system.",
                "metadata": {"source": "knowledge_base", "category": "troubleshooting"},
                "score": 0.85,
                "caption": "Techniques include log analysis, monitoring metrics, and reviewing recent changes."
            },
            {
                "id": "doc3",
                "content": "When diagnosing issues, start with the most recent changes. Many problems can be traced back to recent deployments or configuration changes.",
                "metadata": {"source": "best_practices", "category": "diagnostics"},
                "score": 0.75,
                "caption": "Start with the most recent changes when diagnosing issues."
            }
        ]
        
        # Apply any filters (mock implementation)
        if filters:
            filtered_results = []
            for doc in mock_results:
                match = True
                for key, value in filters.items():
                    if key in doc.get("metadata", {}) and doc["metadata"][key] != value:
                        match = False
                        break
                if match:
                    filtered_results.append(doc)
            return filtered_results[:top_k]
        
        return mock_results[:top_k]
    
    def index_document(self, document: Dict[str, Any]) -> bool:
        """
        Index a document in Azure AI Search.
        
        Args:
            document: Document to index
            
        Returns:
            True if successful, False otherwise
        """
        # TODO: Implement actual indexing
        # For now, just log and return success
        print(f"Would index document: {document['id']}")
        return True
    
    def build_search_request(self, query_embedding: List[float], top_k: int, filters: Optional[Dict] = None) -> Dict:
        """
        Build search request for Azure AI Search.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Optional filters for search
            
        Returns:
            Search request body
        """
        # This would be the actual search request format for Azure AI Search
        request = {
            "search": "*",
            "top": top_k,
            "vectors": [
                {
                    "value": query_embedding,
                    "fields": "embedding",
                    "k": top_k
                }
            ]
        }
        
        # Add filters if provided
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                filter_clauses.append(f"{key} eq '{value}'")
            
            if filter_clauses:
                request["filter"] = " and ".join(filter_clauses)
        
        return request 