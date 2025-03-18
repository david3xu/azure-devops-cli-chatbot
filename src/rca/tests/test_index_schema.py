import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '.env.azure')
load_dotenv(env_file)
print(f"Loaded environment from: {env_file}")

# Get Azure Search settings
search_service = os.getenv("AZURE_SEARCH_SERVICE")
search_index = os.getenv("AZURE_SEARCH_INDEX")
admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
api_version = os.getenv("AZURE_SEARCH_API_VERSION", "2023-11-01")

# Construct the endpoint URL
endpoint = f"https://{search_service}.search.windows.net"
index_url = f"{endpoint}/indexes/{search_index}?api-version={api_version}"

# Set up headers with the admin key
headers = {
    "Content-Type": "application/json",
    "api-key": admin_key
}

print(f"Retrieving schema for index: {search_index}")
print(f"Endpoint: {endpoint}")

# Make the request to get the index definition
try:
    response = requests.get(index_url, headers=headers)
    
    if response.status_code == 200:
        index_def = response.json()
        
        print("\nFields Summary:")
        for field in index_def.get("fields", []):
            field_name = field.get("name")
            field_type = field.get("type")
            searchable = field.get("searchable", False)
            filterable = field.get("filterable", False)
            sortable = field.get("sortable", False)
            facetable = field.get("facetable", False)
            
            print(f"- {field_name} ({field_type})")
            print(f"  Searchable: {searchable}, Filterable: {filterable}, Sortable: {sortable}, Facetable: {facetable}")
            
            # Check for vector search configuration
            if field_type == "Collection(Single)":
                vector_search_dimensions = field.get("dimensions")
                vector_search_profile = field.get("vectorSearchProfile")
                if vector_search_dimensions:
                    print(f"  Vector dimensions: {vector_search_dimensions}")
                if vector_search_profile:
                    print(f"  Vector search profile: {vector_search_profile}")
    else:
        print(f"Error retrieving index: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Exception occurred: {str(e)}")

# Also test a simple search to see document structure
print("\nTesting a simple search to see document structure:")
search_url = f"{endpoint}/indexes/{search_index}/docs/search?api-version={api_version}"
search_payload = {
    "search": "*",
    "top": 1,
    "select": "id,content,category,sourcepage,sourcefile,storageUrl"
}

try:
    response = requests.post(search_url, headers=headers, json=search_payload)
    
    if response.status_code == 200:
        search_results = response.json()
        if search_results.get("value"):
            sample_doc = search_results.get("value", [])[0]
            # Truncate content if it's too long
            if "content" in sample_doc and len(sample_doc["content"]) > 200:
                sample_doc["content"] = sample_doc["content"][:200] + "..."
            print("\nSample Document (without embedding):")
            print(json.dumps(sample_doc, indent=2))
        else:
            print("No documents found in search results")
    else:
        print(f"Error performing search: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Exception occurred during search: {str(e)}") 