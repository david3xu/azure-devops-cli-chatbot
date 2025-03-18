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

### Option 4: Using Deployed App

After setting up the CI/CD pipeline (see [CI_CD_SETUP.md](docs/CI_CD_SETUP.md)), you can test the deployed app:

```bash
# Check health endpoints
curl -v https://uwachatbot-dev.azurewebsites.net/health
curl -v https://uwachatbot-prod.azurewebsites.net/health

# Test the chat API (development)
curl -X POST https://uwachatbot-dev.azurewebsites.net/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Azure DevOps?",
    "conversation_id": "test-session-1",
    "mode": "learn"
  }'

# Test follow-up question (demonstrating context)
curl -X POST https://uwachatbot-dev.azurewebsites.net/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I create a repository?",
    "conversation_id": "test-session-1",
    "mode": "learn"
  }'

# Test command execution (if configured)
curl -X POST https://uwachatbot-dev.azurewebsites.net/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "List all repositories",
    "conversation_id": "execute-session-1",
    "mode": "execute"
  }'
```

#### Testing with Swagger UI

For a more interactive testing experience:

1. Open the Swagger UI in your browser:
   - Development: https://uwachatbot-dev.azurewebsites.net/docs
   - Production: https://uwachatbot-prod.azurewebsites.net/docs

2. Navigate to the `/chat` endpoint and click **Try it out**

3. Enter your request body:
   ```json
   {
     "message": "What is Azure DevOps?",
     "conversation_id": "browser-test-1",
     "mode": "learn"
   }
   ```

4. Click **Execute** and view the response

#### Testing with Postman

For more advanced API testing:

1. Open Postman and create a new request:
   - Method: `POST`
   - URL: `https://uwachatbot-dev.azurewebsites.net/chat`
   - Headers: Add `Content-Type: application/json`

2. In the **Body** tab, select **raw** and **JSON**, then enter:
   ```json
   {
     "message": "What is Azure DevOps?",
     "conversation_id": "postman-test-1",
     "mode": "learn"
   }
   ```

3. Click **Send** and check the response

4. For testing conversation context, keep the same `conversation_id` in subsequent requests

### 💡 Important Note

The chatbot works perfectly fine in **learn-only mode** without actual command execution. This mode explains Azure DevOps CLI commands without attempting to execute them.

To use learn-only mode:
- CLI: This is the default, or explicitly set with `--execution-mode learn`
- API: Include `"mode": "learn"` in your JSON request

## 🔍 Root Cause Analysis (RCA) System

The project now includes a Root Cause Analysis (RCA) system with a Pydantic agent implementation:

### Features

- **Agent-Based Architecture**: Type-safe implementation with Pydantic models
- **RAG Pipeline**: Vector search, document ranking, and response generation
- **Azure Integration**: Connects to Azure OpenAI and Azure AI Search
- **API Endpoints**: FastAPI integration for querying the RCA system

### Using the RCA CLI

Test the RCA system directly with the provided CLI tool:

```bash
# Run a single query
python -m src.rca_cli "What are common causes of server failures?"

# Run in interactive mode
python -m src.rca_cli --interactive

# Run with verbose output for debugging
python -m src.rca_cli --verbose "How to troubleshoot network issues?"
```

### Sending Requests to the API

```bash
curl -X POST "http://localhost:8000/rca/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the root cause of high CPU usage?",
    "max_documents": 5,
    "temperature": 0.7
  }'
```

## Full Documentation

For complete documentation, see the following resources in the `docs` directory:

- [Full Documentation](docs/FULL_DOCUMENTATION.md) - Complete project documentation
- [Development Workflow](docs/DEVELOPMENT_WORKFLOW.md) - Guide for developers
- [Command Execution](docs/COMMAND_EXECUTION.md) - Details on command execution features
- [CI/CD Setup](docs/CI_CD_SETUP.md) - CI/CD pipeline configuration
- [Local Workflow](docs/LOCAL_WORKFLOW.md) - Local development workflow 