# GitHub Workflows

This directory contains the CI/CD workflows for the Azure DevOps CLI Chatbot project.

## Workflow Files

- `ci.yml`: Continuous Integration workflow for testing and building
- `cd.yml`: Continuous Deployment workflow for deploying to development and production

## Required Secrets

To run these workflows successfully, you need to set up the following secrets in your GitHub repository:

### Azure Authentication

- `AZURE_CREDENTIALS`: Service Principal credentials in JSON format
  ```json
  {
    "clientId": "...",
    "clientSecret": "...",
    "subscriptionId": "...",
    "tenantId": "..."
  }
  ```

### Azure Container Registry

- `ACR_REGISTRY`: Your Azure Container Registry URL (e.g., `myregistry.azurecr.io`)
- `ACR_USERNAME`: Username for ACR authentication
- `ACR_PASSWORD`: Password for ACR authentication

## Setting Up Secrets

1. **Create a Service Principal**:
   ```bash
   az login
   az ad sp create-for-rbac --name "devops-chatbot-github" --role "Contributor" \
     --scopes /subscriptions/YOUR_SUBSCRIPTION_ID --sdk-auth
   ```
   Copy the JSON output for the `AZURE_CREDENTIALS` secret.

2. **Get ACR Credentials**:
   ```bash
   ACR_REGISTRY=$(az acr show --name YOUR_ACR_NAME --query loginServer -o tsv)
   ACR_USERNAME=$(az acr credential show --name YOUR_ACR_NAME --query username -o tsv)
   ACR_PASSWORD=$(az acr credential show --name YOUR_ACR_NAME --query "passwords[0].value" -o tsv)
   ```

3. **Add Secrets to GitHub**:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Click "New repository secret" and add each secret

## Troubleshooting

### "Context access might be invalid: AZURE_CREDENTIALS"

If you encounter this error:

1. **Check Secret Availability**:
   - Verify the secret exists in your repository
   - Ensure it has the correct format (valid JSON)
   - Check if the service principal is still active

2. **Permission Issues**:
   - Ensure the service principal has Contributor access to the required resources
   - Check if credential expiration dates are valid

3. **Alternative Authentication**:
   If problems persist, consider using OpenID Connect (OIDC) for Azure authentication:
   ```yaml
   - name: 'Az CLI login'
     uses: azure/login@v1
     with:
       client-id: ${{ secrets.AZURE_CLIENT_ID }}
       tenant-id: ${{ secrets.AZURE_TENANT_ID }}
       subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
   ```
   This requires setting up three separate secrets instead of one JSON secret.

## Environment Setup

The CD workflow uses GitHub environments:
- **development**: For staging deployments
- **production**: For production deployments (requires approval)

Set these up in your repository Settings → Environments.

## Using Existing Azure Resources

If you already have Azure resources and want to use them instead of creating new ones:

### 1. Identify Existing Resources

```bash
# List your existing resource groups
az group list --output table

# List existing App Service plans
az appservice plan list --resource-group YOUR_RESOURCE_GROUP --output table

# List existing web apps
az webapp list --resource-group YOUR_RESOURCE_GROUP --output table

# List existing container registries
az acr list --output table
```

### 2. Get Credentials for Existing Resources

```bash
# Get existing ACR credentials (for your existing registry)
ACR_REGISTRY=$(az acr show --name YOUR_EXISTING_ACR --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name YOUR_EXISTING_ACR --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name YOUR_EXISTING_ACR --query "passwords[0].value" -o tsv)

# Create service principal with access to your existing resources
az ad sp create-for-rbac \
  --name "devops-chatbot-github" \
  --role "Contributor" \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP \
  --sdk-auth
```

### 3. Update Workflow Files

In the workflow YAML files, update the app names to match your existing resources:

```yaml
# Example for cd.yml
- name: Deploy to Azure App Service
  uses: azure/webapps-deploy@v2
  with:
    app-name: 'YOUR_EXISTING_APP_NAME'  # Your existing App Service name
    images: ${{ secrets.ACR_REGISTRY }}/devops-chatbot:${{ github.sha }}
``` 