# Local Development Workflow

This document describes the local development workflow for the Azure DevOps CLI Learning Project with Python Chatbot.

## Overview

The local workflow provides a streamlined process for developing, testing, and preparing the application for deployment to Azure. It bridges the gap between your development environment and the Azure deployment process by validating all components locally before deploying to the cloud.

## Workflow Diagram

```
┌───────────────────┐
│ Local Development │
│ Environment Setup │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐     ┌───────────────────┐
│ Run Tests         │     │ Validate Code     │
│ Locally           ├────►│ Coverage          │
└────────┬──────────┘     └───────────────────┘
         │
         ▼
┌───────────────────┐     ┌───────────────────┐
│ Build Local       │     │ Development       │
│ Docker Image      ├────►│ Container         │
└────────┬──────────┘     └───────────────────┘
         │
         ▼
┌───────────────────┐     ┌───────────────────┐
│ Run Application   │     │ Test API Locally  │
│ in Container      ├────►│ via Web Browser   │
└────────┬──────────┘     └───────────────────┘
         │
         ▼
┌───────────────────┐     ┌───────────────────┐
│ Verify Production │     │ Validate          │
│ Build             ├────►│ Dependencies      │
└────────┬──────────┘     └───────────────────┘
         │
         ▼
┌───────────────────┐
│ Deploy to Azure   │
│ (When Ready)      │
└───────────────────┘
```

## Local Workflow Script

The local workflow is automated through the `.azure/scripts/local_workflow.sh` script, which provides a complete end-to-end process for local development and testing.

### Features

- **Environment Validation**: Ensures all prerequisites are installed
- **Configuration Setup**: Creates and validates environment variables
- **Test Execution**: Runs the test suite with coverage reports
- **Local Containerization**: Builds and runs the application in a Docker container
- **Production Readiness**: Verifies the production build works correctly
- **Deployment Preparation**: Checks Azure configuration before deployment

### Usage

```bash
# Basic usage - runs all workflow steps
bash .azure/scripts/local_workflow.sh

# Skip running tests
bash .azure/scripts/local_workflow.sh --skip-tests

# Skip container build and run
bash .azure/scripts/local_workflow.sh --skip-container

# Show help
bash .azure/scripts/local_workflow.sh --help
```

## Local Development Workflow Steps

### 1. Set Up Local Environment

Before starting development:

- Set up Python virtual environment
- Install required dependencies
- Configure environment variables 
- Verify Azure CLI installation

### 2. Development and Testing

During development:

- Write code and tests
- Run tests regularly to validate functionality
- Run the application locally for interactive testing

### 3. Local Containerization

Before preparing for deployment:

- Build Docker image with development target
- Run the containerized application locally
- Test the API endpoints through browser or tools like curl/Postman
- Validate environment variables are correctly passed to the container

### 4. Pre-Deployment Verification

Before deploying to Azure:

- Verify your Azure CLI login status
- Check the production Docker build succeeds
- Ensure existing resources are correctly imported (if using existing Azure resources)
- Validate all environmental dependencies

### 5. Deployment to Azure (When Ready)

When ready to deploy:

1. Deploy Azure Container Registry:
   ```bash
   bash .azure/scripts/deploy_container_registry.sh
   ```

2. Build and push Docker image:
   ```bash
   bash .azure/scripts/build_push_image.sh [tag]
   ```

3. Deploy App Service:
   ```bash
   bash .azure/scripts/deploy_app_service.sh
   ```

## Benefits of Local Workflow

1. **Reduced Cloud Costs**: Minimize cloud resource usage by validating locally first
2. **Faster Development Cycles**: Quick feedback loop without waiting for cloud deployments
3. **Consistent Environments**: Docker ensures consistency between local and cloud environments
4. **Improved Quality**: Early detection of issues before cloud deployment
5. **Simplified Onboarding**: New developers can quickly set up and understand the workflow

## Troubleshooting

- If Docker build fails, check the Dockerfile and ensure all dependencies are correctly specified
- If tests fail, address the issues before deploying to Azure
- For Azure CLI authentication issues, run `az login` manually
- For missing environment variables, check your `.env` file against `.env.template`

### Azure OpenAI Connectivity Issues

If the chatbot cannot connect to Azure OpenAI, check the following:

1. **Authentication Mode**: Azure OpenAI resources may have key-based authentication disabled. Check and update if needed:
   ```bash
   # Check current authentication settings
   az cognitiveservices account show --name YOUR_OPENAI_RESOURCE_NAME --resource-group YOUR_RESOURCE_GROUP
   
   # Look for "disableLocalAuth": true in the output
   
   # Enable API key authentication if needed
   az resource update --ids /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/YOUR_OPENAI_RESOURCE_NAME --set properties.disableLocalAuth=false
   
   # Verify API keys are available
   az cognitiveservices account keys list --name YOUR_OPENAI_RESOURCE_NAME --resource-group YOUR_RESOURCE_GROUP -o tsv
   ```

2. **Environment Variables**: Ensure your `.env` file has the correct variable names:
   - AZURE_OPENAI_API_KEY (not AZURE_OPENAI_KEY)
   - AZURE_OPENAI_ENDPOINT (without trailing slash)
   - AZURE_OPENAI_DEPLOYMENT_NAME (not AZURE_OPENAI_DEPLOYMENT)

3. **Network Connectivity**: Check network connectivity from your development environment to Azure:
   ```bash
   # Test DNS resolution
   host YOUR_OPENAI_ENDPOINT.replace('https://', '')
   
   # Test HTTPS connectivity
   curl -I https://YOUR_OPENAI_ENDPOINT
   ```

4. **API Versions**: Ensure you're using a supported API version (default is 2023-05-15)

## Integration with CI/CD

The local workflow complements the CI/CD pipeline by:

1. Providing developers with the same validation steps locally that will be run in CI
2. Allowing quick iteration and testing before committing to version control
3. Serving as a testing ground for pipeline changes before implementing them in CI/CD

By following this local workflow, you can ensure a smooth transition from development to deployment, minimizing issues in the cloud environment. 