"""
Script to create the search index in Azure Search.
"""
import os
import sys
import json
import requests
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

from src.rca.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

def create_search_index():
    """Create the search index in Azure Search."""
    # Get Azure Search settings from environment variables
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")  # Use admin key for index creation
    index_name = os.getenv("AZURE_SEARCH_INDEX", "rca-index")
    api_version = "2023-11-01"
    
    if not endpoint or not admin_key:
        logger.error("Missing required Azure Search settings")
        logger.error(f"Endpoint: {'Set' if endpoint else 'Missing'}")
        logger.error(f"Admin Key: {'Set' if admin_key else 'Missing'}")
        return False
    
    # Define the index schema
    index_schema = {
        "name": index_name,
        "fields": [
            {
                "name": "id",
                "type": "Edm.String",
                "key": True,
                "searchable": True,
                "filterable": True,
                "sortable": True,
                "facetable": False
            },
            {
                "name": "content",
                "type": "Edm.String",
                "searchable": True,
                "filterable": False,
                "sortable": False,
                "facetable": False
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
                        "sortable": True,
                        "facetable": True
                    },
                    {
                        "name": "category",
                        "type": "Edm.String",
                        "searchable": True,
                        "filterable": True,
                        "sortable": True,
                        "facetable": True
                    }
                ]
            },
            {
                "name": "contentVector",
                "type": "Collection(Edm.Single)",
                "dimensions": 1536,
                "vectorSearchConfiguration": "vectorConfig"
            }
        ],
        "vectorSearch": {
            "algorithmConfigurations": [
                {
                    "name": "vectorConfig",
                    "kind": "hnsw",
                    "parameters": {
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                }
            ]
        },
        "semantic": {
            "configurations": [
                {
                    "name": "default",
                    "prioritizedFields": {
                        "titleField": {
                            "fieldName": "id"
                        },
                        "contentFields": [
                            {
                                "fieldName": "content"
                            }
                        ],
                        "keywordsFields": [
                            {
                                "fieldName": "metadata/category"
                            },
                            {
                                "fieldName": "metadata/source"
                            }
                        ]
                    }
                }
            ]
        }
    }
    
    # Create the index
    url = f"{endpoint}/indexes/{index_name}?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    
    try:
        # Check if index exists
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Index '{index_name}' already exists")
            return True
        
        # Create the index
        response = requests.put(url, headers=headers, json=index_schema)
        
        if response.status_code == 201:
            logger.info(f"Successfully created index '{index_name}'")
            return True
        else:
            logger.error(f"Failed to create index: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        return False

def index_sample_documents():
    """Index sample documents in the search index."""
    # Get Azure Search settings from environment variables
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")  # Use admin key for indexing
    index_name = os.getenv("AZURE_SEARCH_INDEX", "rca-index")
    api_version = "2023-11-01"
    
    if not endpoint or not admin_key:
        logger.error("Missing required Azure Search settings")
        return False
    
    # Sample documents
    documents = [
        {
            "id": "doc1",
            "content": "This is a sample document about root cause analysis. When investigating issues, start by collecting all relevant logs and metrics.",
            "metadata": {
                "source": "knowledge_base",
                "category": "rca"
            },
            "contentVector": [0.0] * 1536  # Placeholder vector
        },
        {
            "id": "doc2",
            "content": "Common techniques for troubleshooting include log analysis, monitoring metrics, and reviewing recent changes to the system.",
            "metadata": {
                "source": "knowledge_base",
                "category": "troubleshooting"
            },
            "contentVector": [0.0] * 1536  # Placeholder vector
        },
        {
            "id": "doc3",
            "content": "When diagnosing issues, start with the most recent changes. Many problems can be traced back to recent deployments or configuration changes.",
            "metadata": {
                "source": "best_practices",
                "category": "diagnostics"
            },
            "contentVector": [0.0] * 1536  # Placeholder vector
        }
    ]
    
    # Index the documents
    url = f"{endpoint}/indexes/{index_name}/docs/index?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    
    try:
        # Index the documents
        response = requests.post(
            url,
            headers=headers,
            json={"value": documents}
        )
        
        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"Successfully indexed {len(documents)} documents")
            return True
        else:
            logger.error(f"Failed to index documents: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error indexing documents: {str(e)}")
        return False

def main():
    """Main function."""
    print("Creating search index and indexing sample documents...")
    
    # Create the search index
    if create_search_index():
        print("Search index created successfully")
        
        # Index sample documents
        if index_sample_documents():
            print("Sample documents indexed successfully")
        else:
            print("Failed to index sample documents")
    else:
        print("Failed to create search index")

if __name__ == "__main__":
    main() 