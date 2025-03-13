# Azure DevOps CLI Learning Project with Python Chatbot

A comprehensive learning project combining Azure DevOps CLI operations, Python chatbot development with Azure OpenAI, containerization, and CI/CD pipeline implementation.

## Project Overview

This project demonstrates a practical approach to learning and operating Azure DevOps through the development of an intelligent chatbot system. It's architected around several core principles:

1. **CLI-First Workflow**: All Azure DevOps operations are performed through command-line interfaces rather than GUIs, promoting automation and scriptability.

2. **Dual-Purpose Functionality**:
   - **Learn**: Explain Azure DevOps CLI commands with examples and context
   - **Execute**: Directly perform Azure DevOps operations based on natural language requests

3. **Command Execution Engine**: The system contains sophisticated mechanisms to:
   - Interpret natural language requests for Azure DevOps operations
   - Extract parameters from conversation context
   - Securely execute commands with appropriate validations
   - Provide relevant feedback after command execution
   - Handle errors gracefully with helpful guidance

4. **Modern Architecture**: The system is built with a clean, modular architecture following best practices for Python development:
   - Clear separation of concerns
   - Configuration management with environment variables
   - Comprehensive error handling and retry mechanisms
   - Structured logging and metrics collection

5. **Dual-Interface Design**: The chatbot is accessible through both:
   - A CLI for direct terminal interaction
   - A RESTful API for integration with other systems

6. **Cloud-Native Approach**: The application embraces containerization, microservices principles, and cloud deployment patterns:
   - Multi-stage Docker builds
   - Health checks and container optimization
   - CI/CD pipeline automation
   - Metrics and telemetry

7. **AI Integration**: The system leverages Azure OpenAI for intelligent conversation capabilities:
   - Configurable conversation modes
   - Context management with history
   - Token usage optimization
   - Fallback mechanisms for reliability

The project serves as both a learning tool for Azure DevOps CLI commands and a practical example of implementing DevOps practices in a real-world application.

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
python -m uvicorn src.chatbot.api.endpoints.main:app --host 0.0.0.0 --port 8001

# In another terminal, test with curl
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I list repositories in Azure DevOps?", "mode": "learn"}'
```

### Option 3: Using Docker

```bash
# Build and run with Docker
docker build --target development -t devops-chatbot:dev .
docker run -p 8001:8001 --env-file .env devops-chatbot:dev
```

### 💡 Important Note

The chatbot works perfectly fine in **learn-only mode** without actual command execution. This mode explains Azure DevOps CLI commands without attempting to execute them, making it ideal for learning without setting up full Azure DevOps integration.

To use learn-only mode:
- CLI: This is the default, or explicitly set with `--execution-mode learn`
- API: Include `"mode": "learn"` in your JSON request

The command execution functionality can be safely ignored if you're primarily interested in learning about Azure DevOps CLI commands rather than executing them.

## Key Components

- **Azure DevOps CLI Operations**: Learn about and execute DevOps operations through CLI commands
- **Python Chatbot**: Integration with Azure OpenAI for intelligent understanding of requests
- **Command Execution Engine**: Secure execution of Azure DevOps CLI operations based on user requests
- **Containerization**: Docker-based development and production environments
- **CI/CD Pipelines**: Automated testing and deployment workflows
- **Performance Metrics**: Tracking and optimization of chatbot performance

## Setup Instructions

### Prerequisites
- Azure CLI
- Azure DevOps CLI Extension
- Python 3.8+
- Docker
- Azure Subscription with OpenAI access

### Azure OpenAI Configuration

For the chatbot to function correctly, you'll need to set up Azure OpenAI:

1. **Check Authentication Settings**: Ensure your Azure OpenAI resource has API key authentication enabled:
   ```bash
   # Check if disableLocalAuth is set to true
   az cognitiveservices account show --name YOUR_OPENAI_RESOURCE_NAME --resource-group YOUR_RESOURCE_GROUP
   
   # If disableLocalAuth is true, enable API key authentication with:
   az resource update --ids /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/YOUR_OPENAI_RESOURCE_NAME --set properties.disableLocalAuth=false
   ```

2. **Required Environment Variables**:
   - `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
   - `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint (without trailing slash)
   - `AZURE_OPENAI_DEPLOYMENT_NAME`: Your model deployment name
   - `AZURE_OPENAI_API_VERSION`: API version (default: 2023-05-15)

3. **Getting Required Values**:
   ```bash
   # Get your Azure Tenant ID
   az account show --query tenantId -o tsv
   
   # List Azure OpenAI resources and endpoints
   az cognitiveservices account list --query "[?kind=='OpenAI'].[name,properties.endpoint]" -o table
   
   # Get API key (once disableLocalAuth is set to false)
   az cognitiveservices account keys list --name YOUR_OPENAI_RESOURCE_NAME --resource-group YOUR_RESOURCE_GROUP -o tsv
   
   # List deployment names
   az cognitiveservices account deployment list --name YOUR_OPENAI_RESOURCE_NAME --resource-group YOUR_RESOURCE_GROUP -o table
   ```

### Local Development Workflow
Before deploying to Azure, you can use our local development workflow:

```bash
# Run the complete local workflow
bash .azure/scripts/local_workflow.sh

# For more options
bash .azure/scripts/local_workflow.sh --help
```

This workflow:
- Sets up your local environment
- Runs tests
- Builds and runs a Docker container locally
- Prepares for deployment

See [LOCAL_WORKFLOW.md](LOCAL_WORKFLOW.md) for detailed documentation.

### Using the Chat API

The project provides a RESTful API for interacting with the chatbot. Once you've started the server using the local workflow script, you can access the API at:

- API Base URL: http://localhost:8000
- API Documentation: http://localhost:8000/docs (interactive Swagger UI)

#### Start the API Server

**Option 1: Using Docker (via local workflow)**
```bash
bash .azure/scripts/local_workflow.sh
```

**Option 2: Direct Python Execution**
```bash
# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH=$PWD

# Start the API server with hot-reload
python -m uvicorn src.chatbot.api.endpoints.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Testing with Postman

You can test the chatbot API using Postman:

1. **Create a new request**:
   - Method: `POST`
   - URL: `http://localhost:8000/chat`
   - Headers: `Content-Type: application/json`

2. **Configure the JSON body**:
   ```json
   {
     "message": "Tell me about Azure DevOps CLI commands for repositories",
     "conversation_id": "test-session-1",
     "temperature": 0.7
   }
   ```

3. **Send follow-up questions** using the same `conversation_id` to maintain context:
   ```json
   {
     "message": "How do I create a new repository?",
     "conversation_id": "test-session-1"
   }
   ```

4. **Test without conversation_id** to start a new conversation - the API will generate a new ID.

5. **Health endpoint**: Send a GET request to `http://localhost:8000/health` to check API status.

#### Making API Requests from CLI

To interact with the chatbot via the API using curl:

```bash
# Example chat request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I create a work item in Azure DevOps CLI?",
    "conversation_id": "demo-123"
  }'
```

The API documentation at http://localhost:8000/docs provides complete details on all available endpoints, request formats, and response structures.

### Environment Setup
```bash
# Install Azure CLI (instructions at https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)

# Install Azure DevOps CLI Extension
az extension add --name azure-devops

# Authenticate with Azure
az login

# Set default Azure DevOps organization
az devops configure --defaults organization=https://dev.azure.com/YOUR_ORG

# Create a Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Copy .env template and configure
cp .env.template .env
# Edit .env with your Azure OpenAI credentials
```

### Using Development Container (Recommended)

This project includes a Dev Container configuration, which provides a consistent development environment with all dependencies pre-installed. To use it:

1. Install [Visual Studio Code](https://code.visualstudio.com/)
2. Install [Docker](https://www.docker.com/products/docker-desktop)
3. Install the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension for VS Code
4. Open this project in VS Code
5. When prompted, click "Reopen in Container" or run the "Remote-Containers: Reopen in Container" command from the command palette (F1)

The container includes:
- Python 3.8
- Azure CLI with Azure DevOps extension
- Azure Developer CLI (azd)
- JQ for JSON processing
- Bicep CLI
- All necessary VS Code extensions

This approach ensures a consistent environment for all developers and avoids "works on my machine" issues.

For more information, see the [Dev Container README](.devcontainer/README.md).

## Running the Application

### Command Line Interface (CLI)

The project includes a command-line interface for direct interaction with the chatbot:

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run in general assistant mode
python src/cli.py

# Run in Azure DevOps CLI expert mode
python src/cli.py --mode devops-expert

# Adjust response creativity (0.0-1.0)
python src/cli.py --temperature 0.5
```

### Using Docker (Recommended)

Development mode:
```bash
docker build --target development -t devops-chatbot:dev .
docker run -p 8000:8000 --env-file .env -v $(pwd):/app devops-chatbot:dev
```

Production mode:
```bash
docker build --target production -t devops-chatbot:prod .
docker run -p 8000:8000 --env-file .env devops-chatbot:prod
```

### Without Docker

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the API server
python -m uvicorn src.chatbot.api.endpoints.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Usage

The API exposes a `/chat` endpoint that can be used to interact with the chatbot:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I create a work item using Azure DevOps CLI?"}'
```

3. **Send the request** and review the response, which will contain:
   - `message`: The chatbot's response
   - `conversation_id`: Used for maintaining conversation state
   - `timestamp`: When the response was generated

### Using Command Execution Features

The chatbot can both explain Azure DevOps CLI commands and execute them on your behalf. Here's how to use this functionality:

#### Command Execution Through Chat

To execute Azure DevOps CLI operations, simply express your intent in natural language:

```json
{
  "message": "Create a new work item titled 'Update documentation' as a task in project MyProject",
  "conversation_id": "execution-session-1",
  "mode": "execute" 
}
```

The chatbot will:
1. Interpret your request
2. Extract required parameters
3. Ask for any missing information
4. Execute the command after confirmation
5. Return the results with explanation

#### Execution Safety Features

For your security and to prevent unintended consequences:

1. **Confirmation Required**: Potentially destructive operations require explicit confirmation
2. **Parameter Validation**: The system validates parameters before execution
3. **Execution Logging**: All executed commands are logged for auditing
4. **Result Verification**: Command results are verified and formatted for readability

#### Available Command Categories

The following Azure DevOps CLI operations can be executed:

1. **Repository Operations**: Create, list, clone repositories and manage branches
2. **Work Item Management**: Create, update, query, and list work items  
3. **Pipeline Operations**: Run pipelines, check build status, view logs

#### Execution Mode Control

To control whether the chatbot explains commands or executes them:

- Set `"mode": "learn"` to receive explanations only (default)
- Set `"mode": "execute"` to enable command execution
- Set `"mode": "auto"` to let the chatbot determine based on your message

See [COMMAND_EXECUTION.md](COMMAND_EXECUTION.md) for detailed documentation of all executable commands.

## Testing

The project includes unit and integration tests using pytest:

```bash
# Run all tests
python -m pytest

# Run only unit tests
python -m pytest src/tests/unit

# Run with coverage report
python -m pytest --cov=src --cov-report=term --cov-report=html

# Continuous test watching during development
pytest-watch
```

## Implementation Progress

### ✅ Project Foundation
- [x] Create project documentation (README)
- [x] Set up Python virtual environment structure
- [x] Configure environment variables management
- [x] Configure Azure DevOps CLI authentication

### ✅ Python Chatbot Development
- [x] Implement basic conversation flow
- [x] Set up Azure OpenAI integration with error handling and retry logic
- [x] Add structured logging
- [x] Implement API endpoints with FastAPI
- [x] Create CLI interface for terminal interaction

### ✅ Azure OpenAI Integration
- [x] Configure Azure OpenAI resources and authentication
- [x] Implement proper error handling for API calls
- [x] Add token usage tracking and metrics
- [x] Document configuration requirements and troubleshooting

### ✅ Containerization
- [x] Create development Dockerfile
- [x] Implement multi-stage builds
- [ ] Set up container registry
- [x] Configure health checks

### ✅ Azure DevOps CLI Operations
- [x] Implement command execution framework
- [x] Repository operations (create, list, clone, branches)
- [x] Work item operations (create, update, query)
- [x] Pipeline operations (create, run, monitor)
- [ ] Implement project creation and configuration

### ✅ CI/CD Implementation
- [x] Define YAML pipeline configuration
- [x] Set up automated testing
- [x] Configure deployment environments
- [x] Implement security scanning

### 🔄 Performance & Monitoring
- [x] Set up metrics collection framework
- [ ] Implement user feedback mechanism
- [ ] Configure cost monitoring
- [ ] Create performance dashboard

## Project Summary

This project implements a Python-based chatbot for learning and interacting with the Azure DevOps CLI, focusing on key DevOps practices through hands-on implementation.

### Azure DevOps CLI Operations

The project provides a comprehensive set of functions to interact with Azure DevOps through the command line:

#### Repository Operations
```python
# List all repositories in a project
repositories = list_repositories(project="MyProject")

# Create a new repository
new_repo = create_repository(
    name="backend-service",
    project="MyProject",
    init=True,
    default_branch="main"
)

# Clone a repository
clone_repository(
    repository="frontend-app",
    project="MyProject",
    path="./src"
)

# Create a branch
create_branch(
    repository="api-service",
    project="MyProject",
    name="feature/oauth-integration",
    source_branch="main"
)
```

These operations can be executed:
- Directly through Python imports
- Via natural language requests to the chatbot (e.g., "Create a new repository named demo-repo")
- Through the CLI interface

#### Work Item Management
```python
# Create a work item
work_item = create_work_item(
    title="Implement feature X",
    work_item_type="User Story",
    project="MyProject",
    description="As a user, I want to...",
    assigned_to="user@example.com"
)

# Query work items
items = list_work_items(
    work_item_type="Bug",
    state="Active",
    project="MyProject"
)

# Update work items
update_work_item(
    work_item_id=123,
    state="Resolved",
    assigned_to="another_user@example.com"
)
```

The chatbot understands natural language requests and executes them:
- "Create a bug titled 'Fix login issue'"
- "Show me all active tasks assigned to me"
- "Mark work item 123 as resolved" 

#### Pipeline Operations
```python
# List pipelines
pipelines = list_pipelines(project="MyProject")

# Create and run a pipeline
pipeline = create_pipeline(
    name="Build and Test",
    repository="my-repo",
    yaml_path="azure-pipelines.yml"
)
run = run_pipeline(pipeline_id=pipeline["id"])

# Get pipeline logs
logs = get_logs(run_id=run["id"])
```

Pipeline commands can be triggered through conversation:
- "Run the build pipeline for the main branch"
- "Show me the logs from the last deployment"
- "Create a new pipeline for repository X using the default YAML"

All operations include proper error handling, logging, and consistent parameter passing.

### Completed Components

1. **Core Chatbot Architecture**
   - Robust conversation management with context retention
   - Integration with Azure OpenAI service with proper retry logic
   - Comprehensive error handling for API interactions
   - Structured logging for debugging and operational monitoring

2. **Multiple Interface Options**
   - Command-line interface for direct terminal interaction
   - FastAPI-based REST API for integration with other applications
   - Different conversation modes (general and DevOps CLI expert)

3. **Azure DevOps CLI Operations**
   - Command execution framework with proper error handling
   - Repository management (create, list, clone, branch operations)
   - Work item operations (create, update, query, comments)
   - Pipeline management (create, run, monitor, logs)
   - Modular design with consistent error handling and logging

4. **Infrastructure & Deployment**
   - Multi-stage Docker configuration for both development and production
   - Container health checks and security hardening
   - Environment-specific configuration management

5. **Testing Framework**
   - Unit tests with mocking for external service dependencies
   - Test configuration for both quick development testing and coverage reporting

6. **CI/CD Pipeline**
   - GitHub Actions workflows for continuous integration and deployment
   - Automated testing and linting on pull requests and pushes
   - Multi-environment deployment (development and production)
   - Manual approval gates for production deployments
   - Health checks to verify successful deployments
   - See [CI_CD_SETUP.md](CI_CD_SETUP.md) for detailed documentation

### Coming Next

1. **Azure DevOps CLI Project Operations**
   - Project creation and configuration functions
   - Project policy management operations
   - Team and permission management utilities

2. **Enhanced Monitoring**
   - User feedback collection and satisfaction metrics
   - Cost tracking for Azure OpenAI usage
   - Performance dashboards for operational monitoring

3. **Security Enhancements**
   - Secure storage of secrets using Azure Key Vault
   - Automated security scanning in build pipeline
   - Container vulnerability assessment

## Project Structure

```
.
├── .azure/                    # Azure resource management
│   ├── config/                # Azure CLI configuration
│   ├── credentials/           # Securely stored credentials (gitignored)
│   ├── existing-resources/    # Information about existing Azure resources
│   ├── scripts/               # Deployment and management scripts
│   ├── templates/             # Infrastructure as Code templates
│   │   ├── arm/               # ARM templates (JSON)
│   │   └── bicep/             # Bicep templates
│   └── README.md              # Azure-specific documentation
├── .devcontainer/             # Development container configuration
│   ├── Dockerfile             # Container definition
│   ├── devcontainer.json      # VS Code container settings  
│   └── README.md              # Dev container documentation
├── .env.template              # Template for environment variables
├── Dockerfile                 # Multi-stage Dockerfile
├── README.md                  # Project documentation
├── DEVELOPMENT_WORKFLOW.md    # Development process documentation
├── USER_INTERACTIONS.md       # User interaction timeline
├── requirements.txt           # Python dependencies
└── src/                       # Source code
    ├── cli.py                 # Command-line interface
    └── chatbot/               # Chatbot application
        ├── __init__.py        # Package initialization
        ├── api/               # API endpoints and services
        │   ├── endpoints/     # FastAPI endpoints
        │   │   └── main.py    # Main API entry point
        │   └── services/      # Services (OpenAI, etc.)
        │       └── openai_service.py  # Azure OpenAI integration
        ├── config/            # Configuration management
        │   └── settings.py    # Environment settings
        ├── devops_cli/        # Azure DevOps CLI operations
        │   ├── __init__.py    # Package initialization
        │   ├── command_runner.py  # Command execution utilities
        │   ├── repositories.py    # Repository operations
        │   ├── work_items.py      # Work item operations 
        │   ├── pipelines.py       # Pipeline operations
        │   └── operations.py      # Consolidated operations
        ├── models/            # Data models
        │   └── conversation.py # Conversation management
        └── utils/             # Utility functions
            └── logging.py     # Structured logging
```

## Code Structure

### Configuration (`src/chatbot/config/settings.py`)
- **Settings class**: Centralizes application configuration using environment variables
  - `validate()`: Ensures required OpenAI settings are configured
  - `is_production`: Property to determine if running in production environment

### Logging (`src/chatbot/utils/logging.py`)
- **configure_logging()**: Sets up structured logging with different formatters for dev/prod
- **get_logger()**: Returns a configured logger for a specific module
- **log_conversation_metrics()**: Records conversation metrics (duration, tokens, success rate)

### OpenAI Service (`src/chatbot/api/services/openai_service.py`)
- **AzureOpenAIService class**: Handles Azure OpenAI API interactions
  - `initialize()`: Sets up the OpenAI client with proper credentials
  - `_handle_retry()`: Implements exponential backoff retry logic for API calls
  - `chat_completion()`: Makes API requests with error handling and metrics collection

### Conversation Model (`src/chatbot/models/conversation.py`)
- **Message class**: Represents individual messages in a conversation
  - `to_dict()`: Converts message to format required by OpenAI API
- **Conversation class**: Manages conversation state and history
  - `add_user_message()`: Adds user input to conversation history
  - `add_assistant_message()`: Adds AI responses to conversation history
  - `_trim_history()`: Maintains conversation within token limits
  - `get_response()`: Retrieves AI response for current conversation
- **System Prompts**: Pre-defined prompts for different chat modes
  - `DEFAULT_SYSTEM_PROMPT`: General assistant mode
  - `DEVOPS_CLI_EXPERT_PROMPT`: Azure DevOps CLI expert mode

### API Endpoints (`src/chatbot/api/endpoints/main.py`)
- **FastAPI Application**: Main API server with endpoints
  - `health_check()`: API health monitoring endpoint
  - `chat()`: Primary endpoint for conversation interaction
  - `startup_event()`: Initialization tasks when API starts
- **Request/Response Models**:
  - `ChatRequest`: Defines structure of incoming chat requests
  - `ChatResponse`: Defines structure of API responses

### CLI Interface (`src/cli.py`)
- **main()**: Asynchronous entry point for command-line interface
  - Handles command-line arguments (`--mode`, `--temperature`)
  - Manages interactive conversation loop
  - Processes user input and displays responses
  - Provides graceful error handling

### Testing (`src/tests/`)
- **Unit Tests**:
  - `TestMessage`: Validates Message class functionality
  - `TestConversation`: Tests conversation logic including history management
  - Mock-based tests for API interaction without actual OpenAI calls

## Development Workflow

1. All changes are made through feature branches
2. Pull requests require at least one approval
3. Commits follow conventional format: `type: description`
4. Releases use semantic versioning (MAJOR.MINOR.PATCH)

## Cost Management

- Resource tagging for all Azure resources
- Budget alerts for Azure OpenAI usage
- Regular cost optimization reviews

## Troubleshooting

### Azure DevOps CLI Command Structure

When working with the Azure DevOps CLI, it's important to understand the command structure:

1. **Repository Commands**: Use `az repos` (not `az devops repos`)
   ```bash
   # Correct:
   az repos list
   
   # Incorrect:
   az devops repos list
   ```

2. **Most Other Commands**: Use `az devops [resource]`
   ```bash
   # Example:
   az devops project list
   az devops work item create
   ```

This distinction is important when developing or debugging the chatbot. If you encounter errors like:
```
ERROR: 'repos' is misspelled or not recognized by the system.
```
It likely means the command is using the wrong prefix structure.

### OpenAI Connection Issues

If you encounter issues connecting to Azure OpenAI:

1. **Check Authentication Settings**: Ensure API key authentication is enabled:
   ```bash
   az cognitiveservices account show --name YOUR_OPENAI_RESOURCE_NAME --resource-group YOUR_RESOURCE_GROUP
   ```

2. **Verify Environment Variables**:
   - Ensure all required OpenAI variables are set in your `.env` file
   - Check for trailing slashes in the endpoint URL (should not have them)

3. **Test Direct API Access**:
   ```bash
   curl -X POST $AZURE_OPENAI_ENDPOINT/deployments/$AZURE_OPENAI_DEPLOYMENT_NAME/chat/completions?api-version=$AZURE_OPENAI_API_VERSION \
     -H "Content-Type: application/json" \
     -H "api-key: $AZURE_OPENAI_API_KEY" \
     -d '{"messages":[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello!"}]}'
   ```

### Docker Issues

1. **Container Won't Start**: Check environment variables are passed correctly:
   ```bash
   # Using --env-file
   docker run -p 8001:8001 --env-file .env devops-chatbot:local
   
   # Or setting variables individually
   docker run -p 8001:8001 -e AZURE_OPENAI_API_KEY=your_key -e AZURE_OPENAI_ENDPOINT=your_endpoint ... devops-chatbot:local
   ```

2. **API Connection Issues in Container**: Ensure network settings allow outbound connections:
   ```bash
   # Test network connectivity from within container
   docker exec -it container_name curl -v https://api.openai.com
   ```

## Resources

### Azure DevOps Resources
- [Azure DevOps CLI Documentation](https://docs.microsoft.com/en-us/cli/azure/devops)
- [Azure DevOps REST API Reference](https://docs.microsoft.com/en-us/rest/api/azure/devops)
- [Azure Pipelines YAML Schema](https://docs.microsoft.com/en-us/azure/devops/pipelines/yaml-schema)
- [Azure DevOps Best Practices](https://docs.microsoft.com/en-us/azure/devops/pipelines/ecosystems/python)

### AI and OpenAI Integration
- [Azure OpenAI Service Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Prompt Engineering Guidelines](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/prompt-engineering)

### Python Development
- [Python Best Practices Guide](https://docs.python-guide.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Structlog Documentation](https://www.structlog.org/en/stable/)

### Containerization and DevOps
- [Docker Documentation](https://docs.docker.com/)
- [Python Docker Best Practices](https://docs.docker.com/language/python/build-images/)
- [Health Checks for Containers](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Semantic Versioning](https://semver.org/)

## Azure Resource Management

The project includes comprehensive Azure resource management through the `.azure` directory:

### Infrastructure as Code

- **ARM Templates**: JSON-based templates for App Service deployments
- **Bicep Templates**: Bicep-based templates for Container Registry

### Deployment Scripts

- **Azure CLI Configuration**: Sets up Azure CLI defaults and Azure DevOps CLI
- **Container Registry**: Deploys and manages Azure Container Registry
- **App Service**: Deploys containerized application to Azure App Service
- **Docker Image Management**: Builds and pushes images to Azure Container Registry

### Deployment Workflow

1. Configure Azure CLI and DevOps CLI settings
2. Deploy Azure Container Registry using Bicep
3. Build and push Docker image to the registry
4. Deploy Azure App Service using ARM template with container configuration

For detailed instructions, see the [Azure Resource Management README](.azure/README.md).

## CI/CD Setup and Local Testing

This project uses GitHub Actions for continuous integration and deployment. Follow these steps to set up the CI/CD pipeline and test it locally.

### Setting Up GitHub Actions

1. **Create GitHub Environments**:
   - Go to your repository on GitHub > Settings > Environments
   - Create two environments: `development` and `production`
   - For production, add required reviewers for approval protection

2. **Configure GitHub Secrets**:
   - Go to Settings > Secrets and variables > Actions
   - Add the following secrets:
     ```
     AZURE_CREDENTIALS - Service Principal credentials JSON
     ACR_REGISTRY     - Azure Container Registry URL (e.g., myregistry.azurecr.io)
     ACR_USERNAME     - ACR username
     ACR_PASSWORD     - ACR password
     ```

3. **Creating Azure Resources**:
   ```bash
   # Login to Azure
   az login

   # Create Resource Group
   az group create --name devops-chatbot-rg --location eastus

   # Create Container Registry
   az acr create --resource-group devops-chatbot-rg --name devopschatbotacr --sku Basic

   # Create App Service Plan
   az appservice plan create --resource-group devops-chatbot-rg --name devops-chatbot-plan --sku B1 --is-linux

   # Create Web Apps for Dev and Prod
   az webapp create --resource-group devops-chatbot-rg --plan devops-chatbot-plan --name devops-chatbot-dev --runtime "PYTHON|3.8"
   az webapp create --resource-group devops-chatbot-rg --plan devops-chatbot-plan --name devops-chatbot --runtime "PYTHON|3.8"
   ```

### Testing Locally Before Pushing

Before pushing changes to GitHub, test your workflow locally:

1. **Test Linting**:
   ```bash
   pip install flake8
   flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
   flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
   ```

2. **Run Tests**:
   ```bash
   pip install pytest pytest-cov
   pytest src/tests/ --cov=src --cov-report=term
   ```

3. **Build Docker Image**:
   ```bash
   docker build --target development -t devops-chatbot:local .
   docker run -p 8001:8001 --env-file .env -it devops-chatbot:local
   ```

4. **Test the API Health Endpoint**:
   ```bash
   curl http://localhost:8001/health
   ```

5. **Run GitHub Actions Locally** (optional, requires [act](https://github.com/nektos/act)):
   ```bash
   # Install act
   # On macOS: brew install act
   # On Linux: curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

   # Run CI workflow locally
   act -j test
   ```

### Monitoring CI/CD Workflow

Once you push changes to GitHub:

1. Go to the Actions tab in your repository
2. Click on the running workflow to see detailed logs
3. Check each job's output for errors or warnings
4. After CI succeeds, monitor CD progress in the deployment environments

For detailed CI/CD documentation, see [CI_CD_SETUP.md](CI_CD_SETUP.md).

## Contributing

This project is hosted on GitHub and welcomes contributions from the community. Here's how you can contribute:

### Getting the Code

```bash
# Clone the repository
git clone https://github.com/david3xu/azure-devops-cli-chatbot.git
cd azure-devops-cli-chatbot
```

### Development Workflow

1. **Create a branch for your changes**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and commit them**:
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

3. **Push your branch to GitHub**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** on GitHub for review

### Contribution Guidelines

- Follow the existing code style and patterns
- Add tests for new functionality
- Update documentation to reflect your changes
- Keep commits focused and with clear messages
- Reference issue numbers in commit messages where appropriate

### Issues and Feature Requests

If you find a bug or have a feature request, please create an issue on the [GitHub repository](https://github.com/david3xu/azure-devops-cli-chatbot/issues).

When reporting issues, please include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.) 