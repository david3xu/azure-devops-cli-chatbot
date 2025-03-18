"""
Test script for creating an Azure Search index.
This script creates a search index with the necessary fields and sample documents.
"""
import os
import sys
import json
import time
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env.azure
env_file = os.path.join(Path(__file__).resolve().parent.parent.parent.parent, '.env.azure')
if os.path.exists(env_file):
    print(f"Loading environment from {env_file}")
    load_dotenv(env_file)
else:
    print(f"ERROR: .env.azure file not found at {env_file}")
    sys.exit(1)

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

import requests
from src.rca.connectors.embeddings import AzureAdaEmbeddingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_search_index():
    """Create the Azure AI Search index for testing."""
    # Endpoint and API key
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY", "")
    index_name = os.getenv("AZURE_SEARCH_INDEX", "rca-index")
    
    # Verify required settings
    if not endpoint:
        logger.error("Missing required Azure Search settings")
        logger.error(f"Endpoint: {'Set' if endpoint else 'Missing'}")
        logger.error(f"Admin Key: {'Set' if admin_key else 'Missing'}")
        print("Failed to create search index")
        return False
    
    # Print the settings for debugging
    print(f"Using Azure Search endpoint: {endpoint}")
    print(f"Index name: {index_name}")
    print(f"Admin key present: {'Yes' if admin_key else 'No'}")
        
    # Create the index definition
    index_definition = {
        "name": index_name,
        "fields": [
            {
                "name": "id",
                "type": "Edm.String",
                "key": True,
                "searchable": False,
                "filterable": True,
                "sortable": True
            },
            {
                "name": "content",
                "type": "Edm.String",
                "searchable": True,
                "filterable": False,
                "retrievable": True
            },
            {
                "name": "metadata",
                "type": "Edm.ComplexType",
                "fields": [
                    {
                        "name": "source",
                        "type": "Edm.String",
                        "searchable": True,
                        "filterable": True,
                        "retrievable": True
                    },
                    {
                        "name": "category",
                        "type": "Edm.String",
                        "searchable": True,
                        "filterable": True,
                        "retrievable": True
                    }
                ]
            },
            {
                "name": "contentVector",
                "type": "Collection(Edm.Single)",
                "dimensions": 1536,
                "vectorSearchConfiguration": "default"
            }
        ],
        "vectorSearch": {
            "algorithms": [
                {
                    "name": "hnsw",
                    "kind": "hnsw",
                    "parameters": {
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                }
            ],
            "profiles": [
                {
                    "name": "default",
                    "algorithm": "hnsw"
                }
            ]
        },
        "semantic": {
            "configurations": [
                {
                    "name": "default",
                    "prioritizedFields": {
                        "titleField": {"fieldName": "metadata/source"},
                        "prioritizedContentFields": [{"fieldName": "content"}],
                        "prioritizedKeywordsFields": []
                    }
                }
            ]
        }
    }
    
    # Create the index
    try:
        create_url = f"{endpoint}/indexes/{index_name}?api-version=2023-11-01"
        headers = {
            "Content-Type": "application/json",
            "api-key": admin_key
        }
        
        # Check if index already exists
        check_response = requests.get(f"{endpoint}/indexes/{index_name}?api-version=2023-11-01", headers=headers)
        
        if check_response.status_code == 200:
            print(f"Index '{index_name}' already exists. Deleting it first...")
            delete_response = requests.delete(f"{endpoint}/indexes/{index_name}?api-version=2023-11-01", headers=headers)
            if delete_response.status_code != 204:
                print(f"Failed to delete existing index: {delete_response.status_code} - {delete_response.text}")
                return False
            time.sleep(1)  # Wait for deletion to propagate
        
        # Create the index
        response = requests.put(create_url, headers=headers, json=index_definition)
        
        if response.status_code == 201:
            print(f"Index '{index_name}' created successfully")
            
            # Generate embeddings for sample documents
            print("Creating sample documents with embeddings...")
            embedding_service = AzureAdaEmbeddingService()
            
            documents = [
                {
                    "id": "doc1",
                    "content": "This is a sample document about root cause analysis. When investigating issues, start by collecting all relevant logs and metrics.",
                    "metadata": {"source": "knowledge_base", "category": "rca"}
                },
                {
                    "id": "doc2",
                    "content": "Common techniques for troubleshooting include log analysis, monitoring metrics, and reviewing recent changes to the system.",
                    "metadata": {"source": "knowledge_base", "category": "troubleshooting"}
                },
                {
                    "id": "doc3",
                    "content": "When diagnosing issues, start with the most recent changes. Many problems can be traced back to recent deployments or configuration changes.",
                    "metadata": {"source": "best_practices", "category": "diagnostics"}
                }
            ]
            
            # Get embeddings for the documents
            texts = [doc["content"] for doc in documents]
            embeddings = embedding_service.embed_documents(texts)
            
            for i, doc in enumerate(documents):
                doc["contentVector"] = embeddings[i]
            
            # Index the documents
            index_url = f"{endpoint}/indexes/{index_name}/docs/index?api-version=2023-11-01"
            index_payload = {
                "value": documents
            }
            
            index_response = requests.post(index_url, headers=headers, json=index_payload)
            
            if index_response.status_code in (200, 201):
                print(f"Successfully indexed {len(documents)} documents")
                return True
            else:
                print(f"Failed to index documents: {index_response.status_code} - {index_response.text}")
                return False
        else:
            print(f"Failed to create index: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error creating search index: {str(e)}")
        print(f"Error creating search index: {str(e)}")
        return False


if __name__ == "__main__":
    print("Creating search index and indexing sample documents...")
    create_search_index() 