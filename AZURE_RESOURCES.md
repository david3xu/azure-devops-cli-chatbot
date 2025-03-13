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

1. Add the required secrets to GitHub
2. Update the real OpenAI credentials in the App Service settings
3. Push your code to GitHub to trigger the CI/CD pipeline
4. After successful deployment, verify that the health endpoint returns a 200 status

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