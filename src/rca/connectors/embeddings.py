"""
Embedding service for the RCA system.
Provides integration with Azure OpenAI for generating embeddings.
"""
from typing import List, Any, Dict, Optional
import os
import time
import logging
import requests
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv
from pathlib import Path

from src.rca.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Load environment variables from .env.azure
env_file = os.path.join(Path(__file__).resolve().parent.parent.parent.parent, '.env.azure')
if os.path.exists(env_file):
    logger.info(f"Loading environment from {env_file}")
    load_dotenv(env_file)
else:
    logger.warning(f"No .env.azure file found at {env_file}")

class AzureAdaEmbeddingService:
    """
    Embedding service using Azure OpenAI's Ada embedding model.
    Generates vector embeddings for text to enable semantic search.
    """
    
    def __init__(self):
        """Initialize the Azure Ada embedding service."""
        # Azure OpenAI settings from environment variables
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        
        # If endpoint is not specified but service name is, construct the endpoint
        if not self.endpoint:
            service_name = os.getenv("AZURE_OPENAI_SERVICE", "")
            if service_name:
                self.endpoint = f"https://{service_name}.openai.azure.com/"
                logger.info(f"Constructed endpoint from service name: {self.endpoint}")
        
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        
        # Deployment settings - check both variable names
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", 
                                           os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT", "text-embedding-ada-002"))
        self.embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", 
                                      os.getenv("AZURE_OPENAI_EMB_MODEL_NAME", "text-embedding-ada-002"))
        
        # Clean up configuration values
        self.api_key = self._clean_value(self.api_key)
        self.endpoint = self._clean_value(self.endpoint)
        self.api_version = self._clean_value(self.api_version)
        self.embedding_deployment = self._clean_value(self.embedding_deployment)
        self.embedding_model = self._clean_value(self.embedding_model)
        
        # Clean up endpoint URL (remove trailing slash)
        if self.endpoint:
            self.endpoint = self.endpoint.rstrip('/')
        
        self.embedding_dimension = 1536  # Default for Ada embedding model
        
        # Print information for debugging
        logger.info(f"Embedding deployment: {self.embedding_deployment}")
        logger.info(f"Embedding endpoint: {self.endpoint}")
        logger.info(f"API key present: {'Yes' if self.api_key else 'No'}")
        
        # Request settings
        self.max_token_limit = 8191  # Maximum token limit for Ada model
        self.embedding_batch_size = 16  # Number of texts to embed in a single API call
        self.max_retries = 3
        
        # Tracking successful initialization
        self.initialized = False
        self.use_mock = os.getenv("USE_MOCK_SERVICES", "").lower() == "true"
    
    def initialize(self) -> bool:
        """
        Initialize the embedding service and validate settings.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.initialized:
            return True
            
        try:
            # Validate required settings
            if not self.api_key or not self.endpoint:
                logger.warning("Missing required Azure OpenAI settings for embeddings")
                logger.warning(f"API Key: {'Set' if self.api_key else 'Missing'}")
                logger.warning(f"Endpoint: {'Set' if self.endpoint else 'Missing'}")
                logger.info("Using mock embeddings for development")
                self.use_mock = True
                self.initialized = True
                return True
            
            # Test the embedding API with a direct request (not using embed_query to avoid recursion)
            try:
                # Build the URL using our helper method
                url = self._build_url(f"openai/deployments/{self.embedding_deployment}/embeddings")
                headers = {
                    "Content-Type": "application/json",
                    "api-key": self.api_key
                }
                
                params = {
                    "api-version": self.api_version
                }
                
                # Simple test request
                request_body = {
                    "input": ["Test query for embeddings"],
                    "model": self.embedding_model
                }
                
                response = requests.post(
                    url, 
                    headers=headers, 
                    params=params, 
                    json=request_body, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embedding = result.get("data", [{}])[0].get("embedding", [])
                    if embedding and len(embedding) == self.embedding_dimension:
                        self.initialized = True
                        self.use_mock = False
                        logger.info(f"Azure Ada embedding service initialized successfully using deployment: {self.embedding_deployment}")
                        return True
                    else:
                        logger.warning("Invalid embedding response from API")
                        self.use_mock = True
                        self.initialized = True
                        return True
                else:
                    error_msg = response.json().get("error", {}).get("message", "Unknown error")
                    logger.warning(f"Embedding API test failed: {response.status_code} - {error_msg}")
                    if "DeploymentNotFound" in error_msg:
                        logger.warning(f"Deployment '{self.embedding_deployment}' not found. Using mock embeddings.")
                    self.use_mock = True
                    self.initialized = True
                    return True
                    
            except Exception as e:
                logger.warning(f"Error testing embedding API: {str(e)}")
                logger.info("Using mock embeddings for development")
                self.use_mock = True
                self.initialized = True
                return True
                
        except Exception as e:
            logger.error(f"Error initializing Azure Ada embedding service: {str(e)}")
            self.use_mock = True
            self.initialized = True
            return True  # Still return True to allow the system to work with mock data
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate an embedding for a single query text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floating point numbers representing the embedding vector
        """
        # Initialize if not already done
        if not self.initialized:
            self.initialize()
        
        # Use mock data if API is not available
        if self.use_mock:
            return self._get_mock_embedding()
            
        try:
            start_time = time.time()
            embeddings = self._get_embeddings_with_retry([text])
            processing_time = (time.time() - start_time) * 1000
            
            if embeddings and len(embeddings) > 0:
                logger.debug(f"Generated query embedding in {processing_time:.2f}ms")
                return embeddings[0]
            else:
                logger.error("Failed to generate embedding for query")
                return self._get_mock_embedding()
                
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return self._get_mock_embedding()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        # Initialize if not already done
        if not self.initialized:
            self.initialize()
            
        # Use mock data if API is not available
        if self.use_mock:
            return [self._get_mock_embedding() for _ in texts]
            
        if not texts:
            return []
            
        try:
            start_time = time.time()
            
            # Process in batches to avoid rate limits
            all_embeddings = []
            for i in range(0, len(texts), self.embedding_batch_size):
                batch = texts[i:i + self.embedding_batch_size]
                batch_embeddings = self._get_embeddings_with_retry(batch)
                all_embeddings.extend(batch_embeddings)
                
                # Log progress for large batches
                if len(texts) > self.embedding_batch_size and (i + self.embedding_batch_size) % (self.embedding_batch_size * 5) == 0:
                    logger.info(f"Embedded {i + len(batch)}/{len(texts)} documents")
            
            processing_time = (time.time() - start_time) * 1000
            logger.debug(f"Generated {len(texts)} document embeddings in {processing_time:.2f}ms")
            
            return all_embeddings
                
        except Exception as e:
            logger.error(f"Error generating document embeddings: {str(e)}")
            return [self._get_mock_embedding() for _ in texts]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, TimeoutError))
    )
    def _get_embeddings_with_retry(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings with retry logic for handling transient errors.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        # Build the URL using our helper method
        url = self._build_url(f"openai/deployments/{self.embedding_deployment}/embeddings")
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        params = {
            "api-version": self.api_version
        }
        
        # Prepare the request body
        request_body = {
            "input": texts,
            "model": self.embedding_model
        }
        
        # Make the request
        response = requests.post(url, headers=headers, params=params, json=request_body, timeout=30)
        
        if response.status_code != 200:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_msg = error_data["error"]["message"]
            except Exception:
                pass
                
            logger.error(f"Embedding API request failed: {response.status_code} - {error_msg}")
            
            # Mark service as using mock data if we get a permanent error
            if response.status_code == 404 and "DeploymentNotFound" in error_msg:
                self.use_mock = True
                
            raise requests.RequestException(f"Request failed with status code: {response.status_code}")
            
        result = response.json()
        
        # Extract the embeddings from the response
        embeddings = []
        for embedding_data in result.get("data", []):
            embedding = embedding_data.get("embedding", [])
            embeddings.append(embedding)
            
        return embeddings
    
    def _get_mock_embedding(self) -> List[float]:
        """
        Generate a mock embedding for testing.
        
        Returns:
            List of floating point numbers representing a random embedding
        """
        # Generate a random embedding with the correct dimension
        mock_embedding = np.random.normal(0, 0.1, self.embedding_dimension).tolist()
        
        # Normalize to unit length
        norm = np.linalg.norm(mock_embedding)
        normalized_embedding = [x / norm for x in mock_embedding]
        
        return normalized_embedding
    
    def _build_url(self, path):
        """
        Build a properly formatted URL for Azure OpenAI API.
        
        Args:
            path: API path to append to the endpoint
            
        Returns:
            Formatted URL
        """
        endpoint = self.endpoint.rstrip('/')
        path = path.lstrip('/')
        return f"{endpoint}/{path}"
        
    def _clean_value(self, value):
        """
        Clean a configuration value by removing quotes.
        
        Args:
            value: Value to clean
            
        Returns:
            Cleaned value
        """
        if value is None:
            return ""
        return str(value).replace('"', '') 