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
   # Note your Azure OpenAI endpoint, API key, and deployment name
   ```

2. Update the development app settings:
   ```bash
   az webapp config appsettings set --name uwachatbot-dev --resource-group rg-ragagentic \
     --settings \
       AZURE_OPENAI_API_KEY="your-actual-api-key" \
       AZURE_OPENAI_ENDPOINT="https://your-openai-resource.openai.azure.com" \
       AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name"
   ```

3. Update the production app settings (after dev is verified):
   ```bash
   az webapp config appsettings set --name uwachatbot-prod --resource-group rg-ragagentic \
     --settings \
       AZURE_OPENAI_API_KEY="your-actual-api-key" \
       AZURE_OPENAI_ENDPOINT="https://your-openai-resource.openai.azure.com" \
       AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name"
   ```

### 4. Configure Health Check Path

1. Set the health check path for both apps:
   ```bash
   # For development app
   az webapp config set --name uwachatbot-dev --resource-group rg-ragagentic --health-check-path /health

   # For production app
   az webapp config set --name uwachatbot-prod --resource-group rg-ragagentic --health-check-path /health
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
   - Go to Azure Portal → Azure Active Directory → App registrations
   - Create a new registration for GitHub Actions
   - Set up Federated credentials for GitHub

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
   az webapp config container show --name uwachatbot-dev --resource-group rg-ragagentic
   ```

3. Check that WEBSITES_PORT matches the port your app listens on (8001)

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

1. Make sure the app is running with `az webapp restart`
2. Verify the health endpoint is implemented correctly in your code
3. Check application logs for startup errors
4. Try accessing other endpoints to see if the app is running correctly

## Verifying Successful Deployment

A successful deployment should show:

1. **GitHub Actions**: Green checkmarks for all steps in the workflow
2. **Azure Portal**: App Service showing "Running" status
3. **HTTP Status**: 200 OK response from the health endpoint
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