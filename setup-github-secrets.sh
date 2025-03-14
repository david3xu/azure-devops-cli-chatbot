#!/bin/bash
# Script to set up GitHub environment secrets for OIDC authentication

# Exit on error
set -e

echo "Setting up GitHub environment secrets for OIDC authentication..."

# Replace these values or set them as environment variables before running
REPO_NAME=${REPO_NAME:-"david3xu/azure-devops-cli-chatbot"}
APP_NAME=${APP_NAME:-"github-actions-devops-chatbot"}
ACR_NAME=${ACR_NAME:-"ragdemoacruiuvvh33kzw3g"}

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI is not installed. Please install it first."
    echo "Visit: https://cli.github.com/manual/installation"
    exit 1
fi

# Check if logged into GitHub
if ! gh auth status &> /dev/null; then
    echo "Not logged into GitHub CLI. Please login first with 'gh auth login'"
    exit 1
fi

# Check if logged into Azure CLI
if ! az account show &> /dev/null; then
    echo "Not logged into Azure CLI. Please login first with 'az login'"
    exit 1
fi

echo "Fetching Azure information..."

# Get Azure information
APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv)
if [ -z "$APP_ID" ]; then
    echo "Error: Could not find App Registration with name $APP_NAME"
    echo "Make sure the app registration exists or create it first."
    exit 1
fi

TENANT_ID=$(az account show --query "tenantId" -o tsv)
SUBSCRIPTION_ID=$(az account show --query "id" -o tsv)

echo "Fetching ACR information..."
ACR_REGISTRY=$(az acr show --name $ACR_NAME --query loginServer -o tsv 2>/dev/null || echo "")
if [ -z "$ACR_REGISTRY" ]; then
    echo "Error: Could not find Azure Container Registry with name $ACR_NAME"
    exit 1
fi

ACR_USERNAME=$ACR_NAME
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

echo "Found the following values:"
echo "AZURE_CLIENT_ID: $APP_ID"
echo "AZURE_TENANT_ID: $TENANT_ID"
echo "AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
echo "ACR_REGISTRY: $ACR_REGISTRY"
echo "ACR_USERNAME: $ACR_USERNAME"

# Setting up secrets for each environment
for ENV in "development" "production"; do
    echo "Setting up secrets for $ENV environment..."
    
    # Set Azure authentication secrets
    gh secret set AZURE_CLIENT_ID --env $ENV --body "$APP_ID" --repo $REPO_NAME
    gh secret set AZURE_TENANT_ID --env $ENV --body "$TENANT_ID" --repo $REPO_NAME
    gh secret set AZURE_SUBSCRIPTION_ID --env $ENV --body "$SUBSCRIPTION_ID" --repo $REPO_NAME
    
    # Set ACR secrets
    gh secret set ACR_REGISTRY --env $ENV --body "$ACR_REGISTRY" --repo $REPO_NAME
    gh secret set ACR_USERNAME --env $ENV --body "$ACR_USERNAME" --repo $REPO_NAME
    gh secret set ACR_PASSWORD --env $ENV --body "$ACR_PASSWORD" --repo $REPO_NAME
    
    echo "Successfully set up secrets for $ENV environment"
done

echo "All secrets have been set up successfully!"
echo "Your GitHub Actions workflows should now be able to authenticate with Azure using OIDC."
