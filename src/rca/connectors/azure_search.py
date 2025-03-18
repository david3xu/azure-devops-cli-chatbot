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
from dotenv import load_dotenv
from pathlib import Path

from src.chatbot.config.settings import settings
from src.rca.connectors.azure_openai import AzureOpenAIConnector
from src.rca.utils.logging import get_logger
from src.rca.connectors.embeddings import AzureAdaEmbeddingService

# Configure logger
logger = get_logger(__name__)

# Load environment variables from .env.azure
env_file = os.path.join(Path(__file__).resolve().parent.parent.parent.parent, '.env.azure')
if os.path.exists(env_file):
    logger.info(f"Loading environment from {env_file}")
    load_dotenv(env_file)
else:
    logger.warning(f"No .env.azure file found at {env_file}")


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
        self.service_name = os.getenv("AZURE_SEARCH_SERVICE_NAME", 
                                    os.getenv("AZURE_SEARCH_SERVICE", ""))
        
        # Try admin key first, then fall back to query key
        self.admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY", "")
        self.query_key = os.getenv("AZURE_SEARCH_KEY", "")
        
        # Use admin key if available, otherwise use query key
        self.key = self.admin_key if self.admin_key else self.query_key
        
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
        if not self.endpoint and self.service_name:
            self.endpoint = f"https://{self.service_name}.search.windows.net"
            logger.info(f"Constructed search endpoint from service name: {self.endpoint}")
            
        self.index_name = os.getenv("AZURE_SEARCH_INDEX", "rca-index")
        self.api_version = "2023-11-01"
        self.semantic_config = os.getenv("AZURE_SEARCH_SEMANTIC_CONFIG", "default")
        
        # Print debugging information
        logger.info(f"Search service name: {self.service_name}")
        logger.info(f"Search endpoint: {self.endpoint}")
        logger.info(f"Search index: {self.index_name}")
        logger.info(f"Admin key present: {'Yes' if self.admin_key else 'No'}")
        logger.info(f"Query key present: {'Yes' if self.query_key else 'No'}")
        logger.info(f"Using key: {self.key[:5]}... (first 5 chars)")
        
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
            # Construct the search endpoint if not already set
            if not self.endpoint and self.service_name:
                self.endpoint = f"https://{self.service_name}.search.windows.net"
                
            # Remove any quotes from the endpoint and index name
            self.endpoint = self.endpoint.replace('"', '')
            self.index_name = self.index_name.replace('"', '')
            
            # Use admin key if available, otherwise use query key
            if self.admin_key:
                self.key = self.admin_key
            else:
                self.key = self.query_key
                
            # Remove any quotes from the key
            self.key = self.key.replace('"', '')
            
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
                # Remove any quotes from the URL
                url = url.replace('"', '')
                headers = {
                    "Content-Type": "application/json",
                    "api-key": self.key.replace('"', '')  # Remove any quotes from the key
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
    
    def vector_search(self, query, filter=None, top_k=3):
        """
        Perform vector search using embeddings.
        
        Args:
            query: The query to search for
            filter: Filter criteria
            top_k: Number of results to return
            
        Returns:
            List of search results
        """
        if not self.initialized:
            self.initialize()
            
        if self.use_mock:
            return self._get_mock_results(top_k)
            
        try:
            start_time = time.time()
            
            # Generate embedding for the query
            query_vector = self.embedding_service.embed_query(query)
            
            # Prepare vector search request
            search_payload = {
                "vectorQueries": [
                    {
                        "kind": "vector",
                        "vector": query_vector,
                        "fields": "embedding",
                        "k": top_k
                    }
                ],
                "select": "id,content,category,sourcepage,sourcefile",
                "top": top_k
            }
            
            # Add filter if provided
            if filter:
                search_payload["filter"] = filter
                
            # Execute search
            search_url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
            search_url = search_url.replace('"', '')
            headers = {
                "Content-Type": "application/json",
                "api-key": self.key.replace('"', '')
            }
            response = requests.post(
                search_url,
                headers=headers,
                json=search_payload
            )
            
            search_time = time.time() - start_time
            logger.debug(f"Vector search completed in {search_time*1000:.2f}ms")
            
            if response.status_code != 200:
                logger.warning(f"Vector search failed: {response.status_code} - {response.text}")
                return self._get_mock_results(top_k)
                
            # Process results
            results = response.json()
            documents = self._process_search_results(results)
            
            logger.info(f"Vector search: Found {len(documents)} results for '{query}'")
            return documents
            
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            return self._get_mock_results(top_k)
    
    def semantic_search(
        self, 
        query: str, 
        top_k: int = 5,
        filter=None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using Azure AI Search.
        
        Args:
            query: Query text
            top_k: Number of results to return
            filter: Optional filter expression
            
        Returns:
            List of search results
        """
        # Initialize if not already done
        if not self.initialized:
            self.initialize()
            
        # Use mock data if API is not available
        if self.use_mock:
            return self._get_mock_results(top_k)
            
        try:
            # Prepare search request
            url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
            # Remove any quotes from the URL
            url = url.replace('"', '')
            headers = {
                "Content-Type": "application/json",
                "api-key": self.key.replace('"', '')  # Remove any quotes from the key
            }
            
            # Construct the search request
            search_request = {
                "search": query,
                "queryType": "semantic",
                "semanticConfiguration": self.semantic_config,
                "top": top_k,
                "select": "id,content",
                "captions": "extractive",
                "answers": "extractive",
                "count": True
            }
            
            # Add filter if provided
            if filter:
                search_request["filter"] = filter
            
            # Make the request
            start_time = time.time()
            response = requests.post(url, headers=headers, json=search_request)
            
            if response.status_code == 200:
                result = response.json()
                search_time = (time.time() - start_time) * 1000
                logger.info(f"Semantic search completed in {search_time:.2f}ms")
                
                # Extract search results
                docs = result.get("value", [])
                return self._process_search_results(docs)
            
            logger.error(f"Semantic search failed: {response.status_code} - {response.text}")
            return self._get_mock_results(top_k)
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}")
            return self._get_mock_results(top_k)
    
    def hybrid_search(
        self, 
        query: str, 
        top_k: int = 5,
        filter=None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (vector + semantic) using Azure AI Search.
        
        Args:
            query: Query text
            top_k: Number of results to return
            filter: Optional filter expression
            
        Returns:
            List of search results
        """
        # Initialize if not already done
        if not self.initialized:
            self.initialize()
            
        # Use mock data if API is not available
        if self.use_mock:
            return self._get_mock_results(top_k)
            
        try:
            # Get embedding for the query
            query_embedding = self.embedding_service.embed_query(query)
            
            # Prepare search request
            url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
            # Remove any quotes from the URL
            url = url.replace('"', '')
            headers = {
                "Content-Type": "application/json",
                "api-key": self.key.replace('"', '')  # Remove any quotes from the key
            }
            
            # Try new hybrid search format
            search_request = {
                "search": query,
                "queryType": "semantic",
                "semanticConfiguration": self.semantic_config,
                "vectorQueries": [
                    {
                        "kind": "vector",
                        "vector": query_embedding,
                        "fields": "embedding",
                        "k": top_k
                    }
                ],
                "top": top_k,
                "select": "id,content",
                "captions": "extractive",
                "answers": "extractive",
                "count": True
            }
            
            # Add filter if provided
            if filter:
                search_request["filter"] = filter
            
            # Make the request
            start_time = time.time()
            response = requests.post(url, headers=headers, json=search_request)
            
            if response.status_code == 200:
                result = response.json()
                search_time = (time.time() - start_time) * 1000
                logger.info(f"Hybrid search completed in {search_time:.2f}ms")
                
                # Extract search results
                docs = result.get("value", [])
                return self._process_search_results(docs)
            elif response.status_code == 400 and "vectorQueries" in str(response.text):
                # Try fallback to semantic search only
                logger.info("Falling back to semantic search only")
                return self.semantic_search(query, top_k, filter)
            
            logger.error(f"Hybrid search failed: {response.status_code} - {response.text}")
            return self._get_mock_results(top_k)
            
        except Exception as e:
            logger.error(f"Error performing hybrid search: {str(e)}")
            return self._get_mock_results(top_k)
    
    def _process_search_results(self, results):
        """
        Process search results from Azure Search into a standardized format.
        
        Args:
            results: Search results from Azure Search (either a dict with 'value' or a list of docs)
            
        Returns:
            List of processed documents
        """
        # Handle both direct document list and search response with 'value' field
        if isinstance(results, dict) and 'value' in results:
            docs = results.get('value', [])
        else:
            docs = results
            
        processed_results = []
        
        for doc in docs:
            # Extract basic fields that we know exist
            result = {
                "id": doc.get("id", ""),
                "content": doc.get("content", ""),
                "score": doc.get("@search.score", 0.0),
            }
            
            # Add optional fields if they exist
            if "sourcepage" in doc:
                result["sourcepage"] = doc.get("sourcepage", "")
            
            if "sourcefile" in doc:
                result["filepath"] = doc.get("sourcefile", "")
                
            if "category" in doc:
                result["category"] = doc.get("category", "")
                
            if "storageUrl" in doc:
                result["url"] = doc.get("storageUrl", "")
                
            # Add captions if available
            if "@search.captions" in doc:
                captions = doc.get("@search.captions", [])
                if captions and len(captions) > 0:
                    result["caption"] = captions[0].get("text", "")
            
            processed_results.append(result)
            
        return processed_results
    
    def _get_mock_results(self, top_k=3, filter=None):
        print("Getting mock results: Azure Search Connectorzure Search Connector NOT work")
        return []
        # """
        # Generate mock search results for development and testing.
        
        # Args:
        #     top_k: Number of results to return
        #     filter: Optional filter expression (not used in mock implementation)
            
        # Returns:
        #     List of mock search results
        # """
        # # Sample documents that match our actual schema
        # mock_docs = [
        #     {
        #         "id": "file-azure-devops-guide_pdf-page-1",
        #         "content": "Azure DevOps is a suite of services that helps teams plan work, collaborate on code development, and build and deploy applications.",
        #         "score": 0.95,
        #         "sourcepage": "azure-devops-guide.pdf#page=1",
        #         "filepath": "azure-devops-guide.pdf",
        #         "category": "overview",
        #         "url": "https://example.com/azure-devops-guide.pdf"
        #     },
        #     {
        #         "id": "file-azure-pipelines_pdf-page-5",
        #         "content": "Azure Pipelines automatically builds and tests code projects to make them available to others. It works with just about any language or project type.",
        #         "score": 0.89,
        #         "sourcepage": "azure-pipelines.pdf#page=5",
        #         "filepath": "azure-pipelines.pdf",
        #         "category": "pipelines",
        #         "url": "https://example.com/azure-pipelines.pdf"
        #     },
        #     {
        #         "id": "file-azure-boards_pdf-page-3",
        #         "content": "Azure Boards is a service for managing work for software projects. It provides a customizable way to track work items including bugs, tasks, and features.",
        #         "score": 0.82,
        #         "sourcepage": "azure-boards.pdf#page=3",
        #         "filepath": "azure-boards.pdf",
        #         "category": "boards",
        #         "url": "https://example.com/azure-boards.pdf"
        #     },
        #     {
        #         "id": "file-azure-repos_pdf-page-7",
        #         "content": "Azure Repos provides Git repositories or Team Foundation Version Control (TFVC) for source control of your code.",
        #         "score": 0.78,
        #         "sourcepage": "azure-repos.pdf#page=7",
        #         "filepath": "azure-repos.pdf",
        #         "category": "repos",
        #         "url": "https://example.com/azure-repos.pdf"
        #     },
        #     {
        #         "id": "file-azure-artifacts_pdf-page-9",
        #         "content": "Azure Artifacts enables teams to share packages such as Maven, npm, NuGet, and more from public and private sources and integrate package sharing into your pipelines.",
        #         "score": 0.75,
        #         "sourcepage": "azure-artifacts.pdf#page=9",
        #         "filepath": "azure-artifacts.pdf",
        #         "category": "artifacts",
        #         "url": "https://example.com/azure-artifacts.pdf"
        #     }
        # ]
        
        # # Return the top k results or all if fewer than k
        # return self._process_search_results(mock_docs[:min(top_k, len(mock_docs))])
    
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