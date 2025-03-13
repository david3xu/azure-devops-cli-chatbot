# Azure Resources for DevOps Chatbot

This document summarizes the Azure resources that have been set up for the DevOps Chatbot project.

## Resource Group

- **Name**: `rg-ragagentic`
- **Location**: East US

## App Service Plan

- **Name**: `devops-chatbot-plan`
- **SKU**: B1 Basic
- **OS**: Linux

## Web Apps

### Development Environment

- **Name**: `uwachatbot-dev`
- **URL**: https://uwachatbot-dev.azurewebsites.net
- **Python Version**: 3.11
- **Port**: 8001 (configured via WEBSITES_PORT)

### Production Environment

- **Name**: `uwachatbot-prod`
- **URL**: https://uwachatbot-prod.azurewebsites.net
- **Python Version**: 3.11
- **Port**: 8001 (configured via WEBSITES_PORT)

## Container Registry

- **Name**: `ragdemoacruiuvvh33kzw3g`
- **Login Server**: `ragdemoacruiuvvh33kzw3g.azurecr.io`
- **SKU**: Basic
- **Admin Enabled**: Yes

## GitHub Secrets Required

For the CI/CD workflows to function correctly, you need to add the following secrets in your GitHub repository:

1. **ACR_REGISTRY**
   - Value: `ragdemoacruiuvvh33kzw3g.azurecr.io`

2. **ACR_USERNAME**
   - Value: `ragdemoacruiuvvh33kzw3g`

3. **ACR_PASSWORD**
   - Value: The password retrieved from Azure CLI (not shown for security)

4. **AZURE_CREDENTIALS**
   - For this secret, you need to create a service principal with Contributor access to your resource group
   - However, if you don't have permission to create a service principal, you can:
     - Ask your Azure administrator to create one for you
     - Or modify the workflow to use other authentication methods like OpenID Connect

## Environment Variables

Both web apps have the following environment variables configured:

- `AZURE_OPENAI_API_KEY`: Currently set to "placeholder" (update with real key)
- `AZURE_OPENAI_ENDPOINT`: Currently set to "placeholder" (update with real endpoint)
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Currently set to "placeholder" (update with real deployment name)
- `WEBSITES_PORT`: 8001

## Next Steps

Follow these step-by-step instructions to complete the setup and deployment:

### 1. Configure GitHub Secrets

1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret" and add each of the following:

   a. **ACR_REGISTRY**
      - Name: `ACR_REGISTRY`
      - Value: `ragdemoacruiuvvh33kzw3g.azurecr.io`
      - Click "Add secret"

   b. **ACR_USERNAME**
      - Name: `ACR_USERNAME`
      - Value: `ragdemoacruiuvvh33kzw3g`
      - Click "Add secret"

   c. **ACR_PASSWORD**
      - Name: `ACR_PASSWORD`
      - Value: The password retrieved earlier via Azure CLI
      - Click "Add secret"

   d. **AZURE_CREDENTIALS**
      - If you don't have permission to create a service principal, either:
        - Ask your Azure administrator to create one for you, OR
        - Modify the workflow to use OIDC (see below)

### 2. Set Up GitHub Environments

1. Go to GitHub repository → Settings → Environments
2. Create Development Environment:
   - Click "New environment"
   - Name: `development`
   - Click "Configure environment"
   - Add deployment URL: `https://uwachatbot-dev.azurewebsites.net`
   - No protection rules needed
   - Click "Save protection rules"

3. Create Production Environment:
   - Click "New environment"
   - Name: `production`
   - Click "Configure environment"
   - Check "Required reviewers" and add reviewers
   - Add deployment URL: `https://uwachatbot-prod.azurewebsites.net`
   - Click "Save protection rules"

### 3. Update App Service Settings with Real Credentials

1. Get your Azure OpenAI credentials:
   ```bash
   # List Azure OpenAI resources
   az cognitiveservices account list --query "[?kind=='OpenAI'].[name,resourceGroup,location]" -o table
   
   # Get the endpoint
   OPENAI_RESOURCE_NAME="your-openai-resource-name"
   OPENAI_RESOURCE_GROUP="your-openai-resource-group"
   OPENAI_ENDPOINT=$(az cognitiveservices account show --name $OPENAI_RESOURCE_NAME --resource-group $OPENAI_RESOURCE_GROUP --query properties.endpoint -o tsv)
   
   # Get the API key
   OPENAI_KEY=$(az cognitiveservices account keys list --name $OPENAI_RESOURCE_NAME --resource-group $OPENAI_RESOURCE_GROUP --query key1 -o tsv)
   
   # List model deployments
   az cognitiveservices account deployment list --name $OPENAI_RESOURCE_NAME --resource-group $OPENAI_RESOURCE_GROUP -o table
   ```

2. Update the development app settings:
   ```bash
   az webapp config appsettings set --name uwachatbot-dev --resource-group rg-ragagentic \
     --settings \
       AZURE_OPENAI_API_KEY="$OPENAI_KEY" \
       AZURE_OPENAI_ENDPOINT="$OPENAI_ENDPOINT" \
       AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name" \
       AZURE_OPENAI_API_VERSION="2023-05-15"
   ```

3. Update the production app settings (after dev is verified):
   ```bash
   az webapp config appsettings set --name uwachatbot-prod --resource-group rg-ragagentic \
     --settings \
       AZURE_OPENAI_API_KEY="$OPENAI_KEY" \
       AZURE_OPENAI_ENDPOINT="$OPENAI_ENDPOINT" \
       AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name" \
       AZURE_OPENAI_API_VERSION="2023-05-15"
   ```

### 4. Configure Health Check Path

1. Set the health check path for both apps:
   ```bash
   # For development app
   az webapp config set --name uwachatbot-dev --resource-group rg-ragagentic --health-check-path /health --health-check-timeout 60
   
   # Verify health check setting
   az webapp config show --name uwachatbot-dev --resource-group rg-ragagentic --query healthCheckPath

   # For production app
   az webapp config set --name uwachatbot-prod --resource-group rg-ragagentic --health-check-path /health --health-check-timeout 60
   
   # Verify health check setting
   az webapp config show --name uwachatbot-prod --resource-group rg-ragagentic --query healthCheckPath
   ```

### 5. Trigger the Deployment

1. Push your code to the GitHub repository:
   ```bash
   git push origin main
   ```

2. Alternative: Manually trigger the workflow:
   - Go to GitHub repository → Actions → "Continuous Deployment" workflow
   - Click "Run workflow" dropdown
   - Select the branch (main)
   - Click "Run workflow"

3. Monitor the workflow:
   - Go to the Actions tab to watch the progress of the deployment
   - Check that the deployment to development completes successfully
   - Approve the deployment to production when ready

### 6. Alternative: Using OIDC Instead of Service Principal

If you can't create a service principal, modify `.github/workflows/cd.yml`:

1. Replace the Azure login step:
   ```yaml
   - name: Login to Azure
     uses: azure/login@v1
     with:
       client-id: ${{ secrets.AZURE_CLIENT_ID }}
       tenant-id: ${{ secrets.AZURE_TENANT_ID }}
       subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
   ```

2. Add these secrets instead:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`

3. Configure OIDC in Azure:

   a. Create an app registration:
   ```bash
   # Get your subscription ID
   SUBSCRIPTION_ID=$(az account show --query id -o tsv)
   
   # Create app registration
   APP_NAME="github-actions-oidc"
   az ad app create --display-name $APP_NAME
   
   # Get the application ID
   APP_ID=$(az ad app list --display-name $APP_NAME --query "[].appId" -o tsv)
   
   # Create service principal
   az ad sp create --id $APP_ID
   
   # Assign Contributor role
   az role assignment create --assignee $APP_ID \
     --role "Contributor" \
     --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-ragagentic"
   
   # Get tenant ID
   TENANT_ID=$(az account show --query tenantId -o tsv)
   
   echo "Add these secrets to GitHub:"
   echo "AZURE_CLIENT_ID: $APP_ID"
   echo "AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
   echo "AZURE_TENANT_ID: $TENANT_ID"
   ```
   
   b. Configure federated credentials in Azure Portal:
   - Go to Azure Portal → Azure Active Directory → App registrations → $APP_NAME
   - Select "Certificates & secrets" → "Federated credentials"
   - Click "Add credential"
   - Select "GitHub Actions deploying Azure resources" as Scenario
   - Enter details:
     - Organization: YOUR_GITHUB_ORG
     - Repository: YOUR_REPO_NAME
     - Entity type: "Environment"
     - GitHub environment name: "development" (repeat for "production")
     - Name: "github-environment-development" (or "github-environment-production")
   - Click "Add"

   c. Alternative: Use Azure CLI to configure federated credentials:
   ```bash
   # For development environment
   cat > federated-credential-dev.json << EOF
   {
     "name": "github-environment-development",
     "issuer": "https://token.actions.githubusercontent.com",
     "subject": "repo:YOUR_GITHUB_ORG/YOUR_REPO_NAME:environment:development",
     "description": "GitHub Actions deploying to development",
     "audiences": [
       "api://AzureADTokenExchange"
     ]
   }
   EOF
   
   az ad app federated-credential create --id $APP_ID --parameters federated-credential-dev.json
   
   # For production environment
   cat > federated-credential-prod.json << EOF
   {
     "name": "github-environment-production",
     "issuer": "https://token.actions.githubusercontent.com",
     "subject": "repo:YOUR_GITHUB_ORG/YOUR_REPO_NAME:environment:production",
     "description": "GitHub Actions deploying to production",
     "audiences": [
       "api://AzureADTokenExchange"
     ]
   }
   EOF
   
   az ad app federated-credential create --id $APP_ID --parameters federated-credential-prod.json
   ```

4. Update your workflow file to use OIDC authentication with environments:
   ```yaml
   # In .github/workflows/cd.yml

   # For development job
   jobs:
     deploy-dev:
       name: Deploy to Development
       runs-on: ubuntu-latest
       environment: development  # This must match the federated credential
       permissions:
         id-token: write  # Required for OIDC
         contents: read
       
       steps:
         - name: Login to Azure with OIDC
           uses: azure/login@v1
           with:
             client-id: ${{ secrets.AZURE_CLIENT_ID }}
             tenant-id: ${{ secrets.AZURE_TENANT_ID }}
             subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
         
         # ...rest of the workflow...
   
   # Same for production job
   deploy-prod:
     permissions:
       id-token: write
       contents: read
     # ...
   ```

## Testing the Deployment

After deployment, you can test the API with:

```bash
# Check health endpoint
curl https://uwachatbot-dev.azurewebsites.net/health

# Test chat in learn mode
curl -X POST https://uwachatbot-dev.azurewebsites.net/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Azure DevOps?", "mode": "learn"}'
```

## Troubleshooting Common Issues

### 1. Deployment Fails with Authentication Error

If you see "Context access might be invalid: AZURE_CREDENTIALS":

1. Check that the `AZURE_CREDENTIALS` secret exists in GitHub
2. Verify the JSON format is correct (should be the exact output of `az ad sp create-for-rbac`)
3. Ensure the service principal hasn't expired
4. Consider using OIDC authentication instead (see section 6 above)

### 2. Container Deployment Issues

If the app deploys but doesn't start:

1. Check container logs in Azure Portal:
   - Go to App Service → uwachatbot-dev → Container settings → Logs
   - Look for specific error messages

2. Verify container registry access:
   ```bash
   # Check container settings
   az webapp config container show --name uwachatbot-dev --resource-group rg-ragagentic
   
   # If needed, update container settings
   az webapp config container set --name uwachatbot-dev --resource-group rg-ragagentic \
     --docker-registry-server-url https://ragdemoacruiuvvh33kzw3g.azurecr.io \
     --docker-registry-server-user ragdemoacruiuvvh33kzw3g \
     --docker-registry-server-password $(az acr credential show --name ragdemoacruiuvvh33kzw3g --query passwords[0].value -o tsv)
   ```

3. Check that WEBSITES_PORT matches the port your app listens on (8001):
   ```bash
   # Verify app settings
   az webapp config appsettings list --name uwachatbot-dev --resource-group rg-ragagentic --query "[?name=='WEBSITES_PORT']"
   
   # Update if needed
   az webapp config appsettings set --name uwachatbot-dev --resource-group rg-ragagentic --settings WEBSITES_PORT=8001
   ```

4. Check container startup logs:
   ```bash
   # Get logs via CLI
   az webapp log tail --name uwachatbot-dev --resource-group rg-ragagentic
   ```

### 3. OpenAI API Issues

If the app starts but returns errors when calling OpenAI:

1. Verify environment variables are set correctly:
   ```bash
   az webapp config appsettings list --name uwachatbot-dev --resource-group rg-ragagentic
   ```

2. Check the App Service logs for specific error messages:
   - Go to App Service → uwachatbot-dev → Monitoring → Log stream

3. Test direct access to Azure OpenAI from your local machine to verify credentials

### 4. Health Check Fails

If the `/health` endpoint is failing:

1. Make sure the app is running:
   ```bash
   # Restart the app
   az webapp restart --name uwachatbot-dev --resource-group rg-ragagentic
   
   # Check the status
   az webapp show --name uwachatbot-dev --resource-group rg-ragagentic --query state
   ```

2. Verify the health endpoint is implemented correctly in your code:
   ```bash
   # Test the health endpoint directly
   curl -v https://uwachatbot-dev.azurewebsites.net/health
   
   # Check the response code
   curl -s -o /dev/null -w "%{http_code}" https://uwachatbot-dev.azurewebsites.net/health
   ```

3. Check application logs:
   ```bash
   # Stream logs
   az webapp log tail --name uwachatbot-dev --resource-group rg-ragagentic
   
   # Download logs
   az webapp log download --name uwachatbot-dev --resource-group rg-ragagentic
   ```

4. Try hitting the root path and other endpoints:
   ```bash
   # Try root path
   curl -v https://uwachatbot-dev.azurewebsites.net/
   
   # Try docs if available
   curl -v https://uwachatbot-dev.azurewebsites.net/docs
   ```

## Verifying Successful Deployment

A successful deployment should show:

1. **GitHub Actions**: Green checkmarks for all steps in the workflow
2. **Azure Portal**: App Service showing "Running" status
3. **HTTP Status**: 200 OK response from the health endpoint
   ```bash
   # Check health endpoint status code
   curl -s -o /dev/null -w "%{http_code}" https://uwachatbot-dev.azurewebsites.net/health
   
   # Should return "200"
   ```
4. **Log Stream**: No error messages in the application logs
5. **Functionality**: Successful responses from the chat endpoint with meaningful content

To verify the full workflow:

1. Make a change to your code
2. Push to GitHub
3. Watch the CI workflow run and tests pass
4. See the CD workflow automatically deploy to development
5. Test the development deployment
6. Approve the deployment to production
7. Verify the production deployment works correctly 