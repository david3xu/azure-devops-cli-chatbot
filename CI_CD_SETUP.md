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