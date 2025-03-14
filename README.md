# Azure DevOps CLI Learning Project with Python Chatbot

A comprehensive learning project combining Azure DevOps CLI operations, Python chatbot development with Azure OpenAI, containerization, and CI/CD pipeline implementation.

Version: 1.0.0 (Base Application)

[![CI](https://github.com/david3xu/azure-devops-cli-chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/david3xu/azure-devops-cli-chatbot/actions/workflows/ci.yml)
[![CD](https://github.com/david3xu/azure-devops-cli-chatbot/actions/workflows/cd.yml/badge.svg)](https://github.com/david3xu/azure-devops-cli-chatbot/actions/workflows/cd.yml)

**Deployment URLs:**
- Development: [https://uwachatbot-dev.azurewebsites.net](https://uwachatbot-dev.azurewebsites.net)
- Production: [https://uwachatbot-prod.azurewebsites.net](https://uwachatbot-prod.azurewebsites.net)

## 🚀 Quick Start

Get up and running quickly with the Azure DevOps CLI Learning Chatbot in "learn-only" mode:

### Option 1: CLI Interface (Simplest)

```bash
# Clone the repository from GitHub
git clone https://github.com/david3xu/azure-devops-cli-chatbot.git
cd azure-devops-cli-chatbot

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy template and edit)
cp .env.template .env
# Edit .env file with your Azure OpenAI credentials

# Run in learn-only mode (default)
python -m src.cli --mode general
# Or explicitly set learn mode
python -m src.cli --mode general --execution-mode learn
```

### Option 2: API Server

```bash
# Start API server
python -m uvicorn src.chatbot.api.endpoints.main:app --host 0.0.0.0 --port 8000

# In another terminal, test with curl
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I list repositories in Azure DevOps?", "mode": "learn"}'
```

### Option 3: Using Docker

```bash
# Build the development Docker image
docker build --target development -t devops-chatbot:local .

# Run the API server in a container
docker run --rm -d -p 8000:8000 --name devops-api --env-file .env devops-chatbot:local python -m uvicorn src.chatbot.api.endpoints.main:app --host 0.0.0.0 --port 8000

# Test the chat endpoint in learn mode
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Azure DevOps?", "mode": "learn"}'
```

### 💡 Important Note

The chatbot works perfectly fine in **learn-only mode** without actual command execution. This mode explains Azure DevOps CLI commands without attempting to execute them.

To use learn-only mode:
- CLI: This is the default, or explicitly set with `--execution-mode learn`
- API: Include `"mode": "learn"` in your JSON request

## Full Documentation

For complete documentation, see the following resources in the `docs-updates` directory:

- [Full Documentation](docs-updates/FULL_DOCUMENTATION.md) - Complete project documentation
- [Development Workflow](docs-updates/DEVELOPMENT_WORKFLOW.md) - Guide for developers
- [Command Execution](docs-updates/COMMAND_EXECUTION.md) - Details on command execution features
- [CI/CD Setup](docs-updates/CI_CD_SETUP.md) - CI/CD pipeline configuration
- [Local Workflow](docs-updates/LOCAL_WORKFLOW.md) - Local development workflow 