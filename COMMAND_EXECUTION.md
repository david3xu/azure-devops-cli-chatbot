# Command Execution Functionality

This document provides detailed information about the command execution capabilities of the Azure DevOps CLI Chatbot.

## Overview

The chatbot has been designed to not only explain Azure DevOps CLI commands but also execute them on your behalf based on natural language requests. This dual functionality makes it both a learning tool and a productivity tool for working with Azure DevOps.

## Execution Flow

When you request the chatbot to execute a command, the following process occurs:

1. **Intent Recognition**: The chatbot analyzes your request to identify the operation you want to perform.
2. **Parameter Extraction**: It extracts required and optional parameters from your message.
3. **Parameter Validation**: The system validates the extracted parameters.
4. **Confirmation**: For destructive or significant operations, the system requests explicit confirmation.
5. **Execution**: The command is executed using the Azure DevOps CLI.
6. **Result Processing**: Results are formatted for readability and presented back to you.
7. **Error Handling**: Any errors are caught, explained, and suggestions are provided.

## Available Operations

### Repository Operations

| Operation | Description | Example Request |
|-----------|-------------|----------------|
| List Repositories | View all repositories in a project | "Show me all repositories in ProjectX" |
| Create Repository | Create a new repository | "Create a new repository named 'backend-api' in ProjectX" |
| Clone Repository | Clone a repository | "Clone the 'frontend' repository to my local machine" |
| List Branches | View branches in a repository | "Show branches in the 'core-service' repository" |
| Create Branch | Create a new branch | "Create a branch called 'feature/user-auth' in the 'api' repository" |
| Import Repository | Import a repository from GitHub | "Import GitHub repository 'username/repo' to ProjectX" |

### Work Item Operations

| Operation | Description | Example Request |
|-----------|-------------|----------------|
| List Work Items | View work items with filters | "Show me all active bugs assigned to me" |
| Create Work Item | Create a new work item | "Create a user story titled 'Implement login flow' in ProjectX" |
| Update Work Item | Modify an existing work item | "Change work item #123 status to 'Resolved'" |
| Query Work Items | Execute complex queries | "Find all work items related to authentication" |
| Add Comment | Add a comment to a work item | "Add comment 'Fixed in PR #45' to work item #123" |

### Pipeline Operations

| Operation | Description | Example Request |
|-----------|-------------|----------------|
| List Pipelines | View pipelines in a project | "Show me all pipelines in ProjectX" |
| Run Pipeline | Trigger a pipeline execution | "Run the 'nightly-build' pipeline" |
| Get Pipeline Status | Check pipeline run status | "What's the status of the last build pipeline run?" |
| View Logs | View logs from a pipeline run | "Show me the logs from the last deployment pipeline run" |
| Create Pipeline | Create a new pipeline | "Create a pipeline for repository 'api' using the default YAML" |

## Execution Modes

The chatbot supports different execution modes to control its behavior:

- **Learn Mode** (`mode: "learn"`): The chatbot will only explain commands without executing them. This is the default mode.
- **Execute Mode** (`mode: "execute"`): The chatbot will both explain and execute commands.
- **Auto Mode** (`mode: "auto"`): The chatbot will determine whether to execute or just explain based on your message context.

## Authentication and Authorization

Before executing commands, ensure:

1. You are authenticated with Azure DevOps using `az login` and `az devops configure`.
2. You have appropriate permissions for the operations you request.
3. The chatbot service has been configured with the necessary access tokens.

## Security Considerations

- All executed commands are logged for audit purposes.
- Destructive operations (delete, permanent changes) require explicit confirmation.
- The chatbot validates inputs to prevent command injection attacks.
- Sensitive information (tokens, credentials) is never logged or stored.

## Azure DevOps CLI Command Structure

When working with Azure DevOps CLI commands, it's important to understand the correct command structure, which varies depending on the resource type:

### Repository Commands

Repository commands use the format `az repos [command]` (not `az devops repos`):

```bash
# Correct formats:
az repos list
az repos show --repository MyRepo
az repos create --name NewRepo

# Incorrect formats:
az devops repos list
az devops repos show --repository MyRepo
```

### Work Item Commands

Work item commands use the format `az boards [command]`:

```bash
# Correct formats:
az boards work-item create --title "Fix login issue" --type Bug
az boards work-item show --id 123
az boards query --wiql "SELECT [System.Id] FROM workitems"
```

### Pipeline Commands

Pipeline commands use the format `az pipelines [command]`:

```bash
# Correct formats:
az pipelines list
az pipelines run --name "CI Pipeline"
az pipelines show --id 456
```

### Project Commands

Project commands use the format `az devops project [command]`:

```bash
# Correct formats:
az devops project list
az devops project show --project MyProject
az devops project create --name NewProject
```

Understanding these command structures is crucial for troubleshooting when working with the chatbot in execution mode. The chatbot is designed to handle these structural differences automatically, translating your natural language requests into the correct command format.

## Troubleshooting

If command execution fails, the chatbot will:

1. Provide the specific error message from the Azure DevOps CLI.
2. Suggest potential solutions to resolve the issue.
3. Offer to provide more information about the command that failed.

For persistent issues, check:
- Your Azure DevOps CLI authentication status
- Network connectivity to Azure DevOps
- Appropriate permissions for the requested operation

## Examples

### Creating a Work Item

**Request:**
```
Create a bug titled "Login button not working on Firefox" with priority 1 in the Authentication team for project DevOps
```

**Response:**
```
I'll create that bug for you.

Parameters extracted:
- Title: "Login button not working on Firefox"
- Type: Bug
- Priority: 1
- Team: Authentication
- Project: DevOps

Executing command:
az boards work-item create --title "Login button not working on Firefox" --type Bug --project DevOps --assigned-to "" --discussion "Created via DevOps CLI Chatbot" --fields "System.AreaPath=DevOps\\Authentication" "Microsoft.VSTS.Common.Priority=1"

Success! Work item #1234 created.
URL: https://dev.azure.com/organization/DevOps/_workitems/edit/1234
```

### Running a Pipeline

**Request:**
```
Run the production deployment pipeline with variables environment=prod and region=eastus
```

**Response:**
```
I'll run the production deployment pipeline for you.

Parameters extracted:
- Pipeline: production deployment
- Variables:
  - environment: prod
  - region: eastus

This is a production deployment. Are you sure you want to proceed? (yes/no)

> yes

Executing command:
az pipelines run --name "Production Deployment" --variables environment=prod region=eastus

Success! Pipeline run #5678 initiated.
Status: In Progress
URL: https://dev.azure.com/organization/project/_build/results?buildId=5678
``` 