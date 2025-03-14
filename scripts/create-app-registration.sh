# Variables
APP_NAME="github-actions-devops-chatbot"
SUBSCRIPTION_ID="ccc6af52-5928-4dbe-8ceb-fa794974a30f"
RESOURCE_GROUP="rg-ragagentic"
GITHUB_ORG="david3xu"
GITHUB_REPO="azure-devops-cli-chatbot"

# Create app registration and service principal
echo "Creating app registration..."
APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
echo "App ID: $APP_ID"

echo "Creating service principal..."
az ad sp create --id $APP_ID

echo "Assigning Contributor role to the service principal..."
az role assignment create \
  --assignee $APP_ID \
  --role Contributor \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP

# Create federated credential for development environment
echo "Creating federated credential for development environment..."
az ad app federated-credential create \
  --id $APP_ID \
  --parameters "{
    \"name\": \"github-actions-development\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:$GITHUB_ORG/$GITHUB_REPO:environment:development\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }"

# Create federated credential for production environment
echo "Creating federated credential for production environment..."
az ad app federated-credential create \
  --id $APP_ID \
  --parameters "{
    \"name\": \"github-actions-production\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:$GITHUB_ORG/$GITHUB_REPO:environment:production\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }"

echo "App registration and federated credentials created successfully!"
echo "Now you can run the setup-github-secrets.sh script."
