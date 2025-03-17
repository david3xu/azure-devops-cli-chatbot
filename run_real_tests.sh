#!/bin/bash

# Load Azure environment variables
echo "Loading Azure settings from .env.azure..."
export $(cat .env.azure | grep -v "^#" | xargs)

# Echo key settings
echo "Using Azure OpenAI Service: $AZURE_OPENAI_SERVICE"
echo "Embedding deployment: $AZURE_OPENAI_EMB_DEPLOYMENT"
echo "Search service: $AZURE_SEARCH_SERVICE"
echo "API endpoint: $AZURE_OPENAI_ENDPOINT"
echo "Search endpoint: https://${AZURE_SEARCH_SERVICE}.search.windows.net"
echo "Using real Azure resources - NO MOCK MODE"

# Run tests with real Azure services
echo -e "\n=== Running embeddings test with real Azure OpenAI ==="
cd src/rca/tests && python -m test_real_embeddings

echo -e "\n=== Running search test with real Azure Search ==="
python -m test_real_search

echo -e "\n=== Running minimal test with real services ==="
python -m test_minimal

echo -e "\n=== Done ===" 