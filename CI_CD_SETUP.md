# CI/CD Setup for Azure DevOps CLI Chatbot

This document explains the Continuous Integration and Continuous Deployment (CI/CD) workflow setup for the Azure DevOps CLI Chatbot project.

## Overview

The project uses GitHub Actions to implement CI/CD with the following workflow:

1. **Continuous Integration (CI)**: Triggered on every push to `main` and pull requests
2. **Continuous Deployment (CD)**: Triggered after successful CI runs on the `main` branch
3. **Multiple Environments**: Deployment to development and production environments

## Workflow Files

The CI/CD pipeline is defined in two workflow files:

- `.github/workflows/ci.yml`: Handles testing and building
- `.github/workflows/cd.yml`: Handles deployment to different environments

## CI Workflow

The CI workflow does the following:

1. **Lint Code**: Uses Flake8 to check for syntax errors and enforce coding standards
2. **Run Tests**: Executes all tests using pytest with coverage reporting
3. **Build Docker Image**: Creates a Docker image without pushing it (verification only)

The CI workflow runs on:
- Every push to the `main` branch
- Every pull request targeting the `main` branch
- Manual triggering via workflow_dispatch

## CD Workflow

The CD workflow does the following:

1. **Deploy to Development**:
   - Builds and pushes Docker image to Azure Container Registry
   - Deploys to development App Service
   - Runs health check to verify deployment

2. **Deploy to Production** (requires approval):
   - Uses the same image built for development
   - Deploys to production App Service after approval
   - Runs health check to verify deployment

The CD workflow is triggered:
- After a successful CI workflow run on the `main` branch
- Manual triggering via workflow_dispatch

## Required Secrets

To use these workflows, you need to set up the following GitHub secrets:

### Azure Credentials
- `AZURE_CREDENTIALS`: Service Principal credentials for Azure authentication

### Azure Container Registry (ACR)
- `ACR_REGISTRY`: URL of your ACR (e.g., `myregistry.azurecr.io`)
- `ACR_USERNAME`: Username for ACR
- `ACR_PASSWORD`: Password for ACR

## Setting Up Required Secrets

### Create a Service Principal for Azure

```bash
# Login to Azure
az login

# Create a service principal with Contributor role
az ad sp create-for-rbac \
  --name "devops-chatbot-github" \
  --role "Contributor" \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
  --sdk-auth
```

Copy the JSON output and store it as the `AZURE_CREDENTIALS` secret in GitHub.

### Get ACR Credentials

```bash
# Get ACR registry URL
ACR_REGISTRY=$(az acr show --name YOUR_ACR_NAME --query loginServer -o tsv)

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name YOUR_ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name YOUR_ACR_NAME --query "passwords[0].value" -o tsv)
```

Store these values as `ACR_REGISTRY`, `ACR_USERNAME`, and `ACR_PASSWORD` secrets in GitHub.

## Environments Configuration

In GitHub, configure two environments:

1. **development**:
   - No approval required
   - Add any environment-specific variables

2. **production**:
   - Require approvals before deployment
   - Add environment-specific variables
   - Add environment URL for easy access

## Monitoring Deployments

1. Monitor workflow runs in the "Actions" tab of the GitHub repository
2. Check deployment status in Azure App Service
3. Verify health using the `/health` endpoint on each environment

## Workflow Diagram

```
┌─────────────┐     ┌────────────┐     ┌────────────────┐     ┌────────────────┐
│  Code Push  │────▶│  CI Build  │────▶│  Dev Deploy    │────▶│ Prod Approval  │
└─────────────┘     │  & Test    │     │  (Automatic)   │     │  & Deployment  │
                    └────────────┘     └────────────────┘     └────────────────┘
```

## Security Considerations

- Service principals follow the principle of least privilege
- Secrets are securely stored in GitHub
- Production deployments require manual approval
- Health checks verify successful deployments

## Troubleshooting

If workflows fail, check:

1. **Linting Issues**: Fix any syntax or style issues reported by Flake8
2. **Test Failures**: Debug failed tests locally before pushing
3. **Docker Build Issues**: Make sure Dockerfile is correct
4. **Deployment Failures**: Check Azure credentials and App Service configuration
5. **Health Check Failures**: Verify that the application starts correctly 

## Using Existing Azure Resources

Instead of creating new Azure resources, you can utilize your existing infrastructure for deployment. This section explains how to integrate the CI/CD workflow with existing Azure resources.

### 1. Identify Existing Resources

First, identify the existing resources you want to use:

```bash
# List resource groups
az group list --query "[].{Name:name, Location:location}" -o table

# List App Service plans in a resource group
az appservice plan list --resource-group YOUR_RESOURCE_GROUP --query "[].{Name:name, SKU:sku.name, Capacity:sku.capacity}" -o table

# List Web Apps
az webapp list --resource-group YOUR_RESOURCE_GROUP --query "[].{Name:name, DefaultHostName:defaultHostName, State:state}" -o table

# List Container Registries
az acr list --query "[].{Name:name, LoginServer:loginServer, AdminEnabled:adminUserEnabled}" -o table
```

### 2. Configure Existing Web Apps for Containers

Ensure your existing App Services are configured to use container deployment:

```bash
# Enable container settings on existing web app
az webapp config container set \
  --name YOUR_EXISTING_DEV_APP \
  --resource-group YOUR_RESOURCE_GROUP \
  --enable-app-service-storage true \
  --docker-registry-server-url https://YOUR_ACR_REGISTRY

# Same for production app
az webapp config container set \
  --name YOUR_EXISTING_PROD_APP \
  --resource-group YOUR_RESOURCE_GROUP \
  --enable-app-service-storage true \
  --docker-registry-server-url https://YOUR_ACR_REGISTRY
```

### 3. Set Correct Application Settings

Make sure your apps have the necessary environment variables:

```bash
# Set application settings for development app
az webapp config appsettings set \
  --name YOUR_EXISTING_DEV_APP \
  --resource-group YOUR_RESOURCE_GROUP \
  --settings \
    AZURE_OPENAI_API_KEY="placeholder" \
    AZURE_OPENAI_ENDPOINT="placeholder" \
    AZURE_OPENAI_DEPLOYMENT_NAME="placeholder" \
    WEBSITES_PORT=8001

# Same for production with appropriate values
az webapp config appsettings set \
  --name YOUR_EXISTING_PROD_APP \
  --resource-group YOUR_RESOURCE_GROUP \
  --settings \
    AZURE_OPENAI_API_KEY="placeholder" \
    AZURE_OPENAI_ENDPOINT="placeholder" \
    AZURE_OPENAI_DEPLOYMENT_NAME="placeholder" \
    WEBSITES_PORT=8001
```

### 4. Update Workflow Files

Modify the workflow files to use your existing resources:

1. **Update `cd.yml`**:
   
   ```yaml
   # Development deployment
   - name: Deploy to Azure App Service
     uses: azure/webapps-deploy@v2
     with:
       app-name: 'YOUR_EXISTING_DEV_APP'  # Your existing development app
       images: ${{ secrets.ACR_REGISTRY }}/devops-chatbot:${{ github.sha }}
   
   # Production deployment
   - name: Deploy to Azure App Service
     uses: azure/webapps-deploy@v2
     with:
       app-name: 'YOUR_EXISTING_PROD_APP'  # Your existing production app
       images: ${{ secrets.ACR_REGISTRY }}/devops-chatbot:${{ github.sha }}
   ```

2. **Update Health Check URLs**:
   
   ```yaml
   - name: Run Health Check
     run: |
       sleep 60  # Wait for deployment to be ready
       curl -f https://YOUR_EXISTING_DEV_APP.azurewebsites.net/health || exit 1
   ```

### 5. Get Existing Resource Credentials

Collect the credentials needed for GitHub Secrets:

```bash
# Get Container Registry credentials
ACR_REGISTRY=$(az acr show --name YOUR_EXISTING_ACR --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name YOUR_EXISTING_ACR --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name YOUR_EXISTING_ACR --query "passwords[0].value" -o tsv)

# Create service principal for GitHub Actions
# Use a more targeted scope to your specific resource group
az ad sp create-for-rbac \
  --name "devops-chatbot-github" \
  --role "Contributor" \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP \
  --sdk-auth
```

### 6. Configure GitHub Environments

Create environments in GitHub that match your existing resources:

1. **Development Environment**:
   - Name: `development`
   - URL: `https://YOUR_EXISTING_DEV_APP.azurewebsites.net`
   - No protection rules needed

2. **Production Environment**:
   - Name: `production`
   - URL: `https://YOUR_EXISTING_PROD_APP.azurewebsites.net`
   - Add required reviewers for protection

### 7. Verify Web App Configuration

Check that your App Service can properly host the containerized application:

```bash
# Verify container settings
az webapp config container show \
  --name YOUR_EXISTING_DEV_APP \
  --resource-group YOUR_RESOURCE_GROUP

# Ensure app is running Linux
az webapp show \
  --name YOUR_EXISTING_DEV_APP \
  --resource-group YOUR_RESOURCE_GROUP \
  --query "kind"
```

By using existing resources, you can save costs and integrate the project with your current infrastructure. Just ensure the resources meet the necessary requirements (Python support, Linux, container compatibility).

## Local Testing Before Pushing

Before pushing changes that trigger the CI/CD workflows, test your changes locally to ensure they pass:

### Testing Locally

#### 1. Run Linting Checks

```bash
# Install flake8 if needed
pip install flake8

# Run critical error check
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Run full style check (optional)
flake8 . --count --max-complexity=10 --max-line-length=127 --statistics

# Run just on source code to avoid dependency issues
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
```

#### 2. Run Tests

```bash
# Install pytest and coverage
pip install pytest pytest-cov

# Run tests with coverage
export PYTHONPATH=$PWD && python -m pytest src/tests/ --cov=src --cov-report=term
```

#### 3. Build and Test Docker Image

```bash
# Build development image
docker build --target development -t devops-chatbot:local .

# Test the built image works
docker run --rm -it devops-chatbot:local python -c "import sys; print(f'Python version: {sys.version}'); import src; print('Successfully imported src package')"

# Start the API server in a container
docker run --rm -d -p 8001:8001 --name devops-api devops-chatbot:local python -m uvicorn src.chatbot.api.endpoints.main:app --host 0.0.0.0 --port 8001

# Test the health endpoint
curl -X GET http://localhost:8001/health

# Test the chat endpoint (learn mode)
curl -X POST http://localhost:8001/chat -H "Content-Type: application/json" -d '{"message": "What is Azure DevOps?", "mode": "learn"}'

# Clean up
docker stop devops-api
```

### Testing GitHub Actions Locally

You can also test GitHub Actions workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
# On macOS: brew install act
# On Linux: curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run the entire CI workflow
act -j test

# Run specific jobs
act -j lint
act -j build

# Run with specific event
act pull_request -j test
```

When using `act`, remember that:
- You might need to provide secrets in a `.secrets` file
- Some GitHub-specific features might not work locally
- Running with `-n` performs a dry run without executing actions

By testing locally first, you can catch issues before they trigger the CI/CD workflow, saving time and ensuring smooth deployments. 